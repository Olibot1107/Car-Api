#!/usr/bin/env python3
"""Camera-driven autonomous navigation loop for the car.

This script keeps the latest camera frame in a background thread, scores the
left/center/right regions for likely free space, and drives the car toward the
clearest path. It is intentionally simple and lightweight so it can run on the
same device that hosts the car controls.
"""

import argparse
import logging
import signal
import threading
import time

import cv2

from lib.movement import CarControl


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class LatestFrameCamera:
    """Continuously grab the newest frame so navigation never trails behind."""

    def __init__(self, index=0, width=320, height=240):
        self.index = index
        self.width = width
        self.height = height
        self.capture = None
        self.thread = None
        self.running = False
        self.lock = threading.Lock()
        self.latest_frame = None

    def start(self):
        self.capture = cv2.VideoCapture(self.index)
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open camera index {self.index}")

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.running = True
        self.thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.thread.start()

    def _reader_loop(self):
        try:
            while self.running:
                success, frame = self.capture.read()
                if not success:
                    time.sleep(0.05)
                    continue

                with self.lock:
                    self.latest_frame = frame
        finally:
            if self.capture is not None:
                self.capture.release()
                self.capture = None

    def read(self):
        with self.lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame.copy()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)


class CameraNavigator:
    """Very small vision navigator that steers toward the clearest region."""

    def __init__(
        self,
        car,
        cruise_speed=35,
        reverse_speed=25,
        stop_threshold=78.0,
        turn_margin=6.0,
    ):
        self.car = car
        self.cruise_speed = cruise_speed
        self.reverse_speed = reverse_speed
        self.stop_threshold = stop_threshold
        self.turn_margin = turn_margin
        self.center_angle = 100
        self.left_angle = 70
        self.right_angle = 130

    def score_frame(self, frame):
        """Return a simple free-space score for left, center, and right zones."""
        frame = cv2.resize(frame, (320, 240), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(gray, 50, 150)

        # Focus on the lower half of the frame where obstacles are most relevant.
        lower_y = int(gray.shape[0] * 0.45)
        gray = gray[lower_y:, :]
        edges = edges[lower_y:, :]

        third = gray.shape[1] // 3
        zones = {
            "left": (slice(None), slice(0, third)),
            "center": (slice(None), slice(third, third * 2)),
            "right": (slice(None), slice(third * 2, gray.shape[1])),
        }

        scores = {}
        for name, (ys, xs) in zones.items():
            gray_roi = gray[ys, xs]
            edge_roi = edges[ys, xs]

            # Higher values mean more clutter, so we want to steer toward the
            # lowest score.
            edge_score = cv2.mean(edge_roi)[0] / 255.0 * 100.0
            darkness_score = (255.0 - cv2.mean(gray_roi)[0]) / 255.0 * 100.0
            scores[name] = (edge_score * 0.7) + (darkness_score * 0.3)

        return scores

    def choose_action(self, scores):
        ordered = sorted(scores.items(), key=lambda item: item[1])
        best_name, best_score = ordered[0]
        second_score = ordered[1][1]
        center_score = scores["center"]
        confidence = second_score - best_score

        if center_score >= self.stop_threshold:
            return "recover", best_name, confidence

        if best_name == "left" and confidence >= self.turn_margin:
            return "left", best_name, confidence
        if best_name == "right" and confidence >= self.turn_margin:
            return "right", best_name, confidence

        return "forward", best_name, confidence

    def execute(self, action):
        if action == "left":
            self.car.set_steering(self.left_angle)
            self.car.forward()
            self.car.set_speed(self.cruise_speed)
        elif action == "right":
            self.car.set_steering(self.right_angle)
            self.car.forward()
            self.car.set_speed(self.cruise_speed)
        elif action == "recover":
            self.car.stop()
            time.sleep(0.2)
            self.car.backward()
            self.car.set_speed(self.reverse_speed)
            time.sleep(0.35)
            self.car.stop()
            time.sleep(0.1)
        else:
            self.car.center_steering()
            self.car.forward()
            self.car.set_speed(self.cruise_speed)


def parse_args():
    parser = argparse.ArgumentParser(description="Camera-driven autonomous navigation")
    parser.add_argument("--camera-index", type=int, default=0, help="Camera device index")
    parser.add_argument("--width", type=int, default=320, help="Camera capture width")
    parser.add_argument("--height", type=int, default=240, help="Camera capture height")
    parser.add_argument("--speed", type=int, default=35, help="Cruise speed percentage")
    parser.add_argument("--reverse-speed", type=int, default=25, help="Reverse speed percentage")
    parser.add_argument("--show", action="store_true", help="Show a debug window")
    return parser.parse_args()


def main():
    args = parse_args()
    stop_requested = False

    def handle_signal(signum, frame):
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    car = None
    camera = None

    try:
        logger.info("Starting autonomous navigation")
        car = CarControl()
        camera = LatestFrameCamera(args.camera_index, args.width, args.height)
        camera.start()

        navigator = CameraNavigator(
            car=car,
            cruise_speed=args.speed,
            reverse_speed=args.reverse_speed,
        )

        car.center_steering()
        car.forward()
        car.set_speed(args.speed)

        while not stop_requested:
            frame = camera.read()
            if frame is None:
                car.stop()
                time.sleep(0.05)
                continue

            scores = navigator.score_frame(frame)
            action, best_zone, confidence = navigator.choose_action(scores)
            navigator.execute(action)

            logger.debug(
                "zones=%s best=%s confidence=%.1f action=%s",
                {k: round(v, 1) for k, v in scores.items()},
                best_zone,
                confidence,
                action,
            )

            if args.show:
                overlay = cv2.resize(frame, (320, 240), interpolation=cv2.INTER_AREA)
                for idx, (name, score) in enumerate(sorted(scores.items())):
                    cv2.putText(
                        overlay,
                        f"{name}: {score:.1f}",
                        (10, 20 + idx * 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        1,
                        cv2.LINE_AA,
                    )
                cv2.imshow("Autonomous Navigation", overlay)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            time.sleep(0.1)

    except Exception as e:
        logger.error("Autonomous navigation failed: %s", e)
    finally:
        if car is not None:
            try:
                car.stop()
                car.center_steering()
            except Exception:
                pass
        if camera is not None:
            camera.stop()
        if args.show:
            cv2.destroyAllWindows()
        logger.info("Autonomous navigation stopped")


if __name__ == "__main__":
    main()
