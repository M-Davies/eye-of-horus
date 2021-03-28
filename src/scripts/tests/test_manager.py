# --------------------------------------------------------------------
# Runs the pytest suite against the main python management script
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under GNU GPL v3 License
# --------------------------------------------------------------------

import sys
import pytest
import logging
import os

from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.getenv('ROOT_DIR') + "/src/scripts")
from manager import main, parseArgs  # noqa: E402
sys.path.append(os.getenv('ROOT_DIR') + "/src/scripts/gesture")
from gesture_recog import projectHandler  # noqa: E402

TEST_IMAGE_DIR = f"{os.getenv('ROOT_DIR')}/src/scripts/tests/metadata"


# Before running any tests, to save time, setup the project before we do anything
@pytest.fixture(scope="session", autouse=True)
def setup_module():
    logging.getLogger().info("[INFO] Starting Rekognition project before running tests...")
    with pytest.raises(SystemExit):
        projectHandler(True)


def readResponseFile():
    with open(f"{os.getenv('ROOT_DIR')}/src/scripts/response.json", "r") as logfile:
        return dict(logfile.read())


class TestManagerCreate:
    # Checks test user was successfully created
    def test_user_create_success(self):
        args = parseArgs([
            "-a", "create",
            "-m",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg", f"{TEST_IMAGE_DIR}/test_lock_2.jpg", f"{TEST_IMAGE_DIR}/test_lock_3.jpg", f"{TEST_IMAGE_DIR}/test_lock_4.jpg",
            "-u", f"{TEST_IMAGE_DIR}/test_unlock_1.jpg", f"{TEST_IMAGE_DIR}/test_unlock_2.jpg", f"{TEST_IMAGE_DIR}/test_unlock_3.jpg", f"{TEST_IMAGE_DIR}/test_unlock_4.jpg"
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 0

    # Checks failed create action on missing profile
    def test_user_profile_fail(self):
        args = parseArgs([
            "-m",
            "-a", "create",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_unlock_1.jpg {TEST_IMAGE_DIR}/test_unlock_2.jpg {TEST_IMAGE_DIR}/test_unlock_3.jpg {TEST_IMAGE_DIR}/test_unlock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 13

    # Checks failed create action on missing face
    def test_user_face_fail(self):
        args = parseArgs([
            "-m",
            "-a", "create",
            "-p", "testuser",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_unlock_1.jpg {TEST_IMAGE_DIR}/test_unlock_2.jpg {TEST_IMAGE_DIR}/test_unlock_3.jpg {TEST_IMAGE_DIR}/test_unlock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 13

    # Checks failed create action on missing face file
    def test_user_face_not_exist_fail(self):
        args = parseArgs([
            "-m",
            "-a", "create",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/foobar.jpg",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_unlock_1.jpg {TEST_IMAGE_DIR}/test_unlock_2.jpg {TEST_IMAGE_DIR}/test_unlock_3.jpg {TEST_IMAGE_DIR}/test_unlock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 8

    # Checks failed create action on txt face file
    def test_user_face_not_img_fail(self):
        args = parseArgs([
            "-m",
            "-a", "create",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/placeholder.txt",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_unlock_1.jpg {TEST_IMAGE_DIR}/test_unlock_2.jpg {TEST_IMAGE_DIR}/test_unlock_3.jpg {TEST_IMAGE_DIR}/test_unlock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 7

    # Checks failed create action on missing lock/unlock
    def test_user_gesture_fail(self):
        args = parseArgs([
            "-m",
            "-a", "create",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg",
            "-u", f"{TEST_IMAGE_DIR}/test_unlock_1.jpg {TEST_IMAGE_DIR}/test_unlock_2.jpg {TEST_IMAGE_DIR}/test_unlock_3.jpg {TEST_IMAGE_DIR}/test_unlock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 13

        args = parseArgs([
            "-m",
            "-a", "create",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 13

    # Checks failed create action on missing lock/unlock gesture file
    def test_user_gesture_not_exist_fail(self):
        args = parseArgs([
            "-m",
            "-a", "create",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/foobar.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_unlock_1.jpg {TEST_IMAGE_DIR}/test_unlock_2.jpg {TEST_IMAGE_DIR}/test_unlock_3.jpg {TEST_IMAGE_DIR}/test_unlock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 13

        args = parseArgs([
            "-m",
            "-a", "create",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_unlock_1.jpg {TEST_IMAGE_DIR}/test_unlock_2.jpg {TEST_IMAGE_DIR}/test_unlock_3.jpg {TEST_IMAGE_DIR}/foobar.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 13

    # Checks failed create action on broken combination rules lock/unlock gesture file
    def test_user_gesture_rule_broken_fail_on_create(self):
        args = parseArgs([
            "-m",
            "-a", "create",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_1.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_unlock_1.jpg {TEST_IMAGE_DIR}/test_unlock_2.jpg {TEST_IMAGE_DIR}/test_unlock_3.jpg {TEST_IMAGE_DIR}/test_unlock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 20

        args = parseArgs([
            "-m",
            "-a", "create",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 21

        args = parseArgs([
            "-m",
            "-a", "create",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_lock_4.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_1.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 22


class TestManagerEdit:
    # Checks a test user's face was successfully edited
    def test_user_edit_face_success(self):
        args = parseArgs([
            "-m",
            "-a", "edit",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg"
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 0

    # Checks a test gesture combination was successfully edited
    def test_user_edit_lock_success(self):
        # Lock Gesture
        args = parseArgs([
            "-m",
            "-a", "edit",
            "-p", "testuser",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 0

        # Unlock Gesture
        args = parseArgs([
            "-m",
            "-a", "edit",
            "-p", "testuser",
            "-u", f"{TEST_IMAGE_DIR}/test_lock_4.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_1.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 0

        # All Gesture
        args = parseArgs([
            "-m",
            "-a", "edit",
            "-p", "testuser",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_lock_4.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_1.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 0

    # Checks a full test user edit was successfully achieved
    def test_user_edit_all_success(self):
        args = parseArgs([
            "-m",
            "-a", "edit",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_lock_4.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_1.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 0

    # Checks a test user's name ommited fails
    def test_user_edit_no_username_fail(self):
        args = parseArgs([
            "-m",
            "-a", "edit",
            "-f", f"{TEST_IMAGE_DIR}/foobar.jpg"
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 13

    # Checks a test user's name not exist fails
    def test_user_edit_invalid_user_fail(self):
        args = parseArgs([
            "-m",
            "-a", "edit",
            "-p", "foobar"
            "-f", f"{TEST_IMAGE_DIR}/foobar.jpg"
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 9

    # Checks a test user's face that does not exist fails
    def test_user_edit_face_not_exist_fail(self):
        args = parseArgs([
            "-m",
            "-a", "edit",
            "-p", "foobar"
            "-f", f"{TEST_IMAGE_DIR}/foobar.jpg"
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 8

    # Checks a test user's face that is not an image fails
    def test_user_edit_face_not_image_fail(self):
        args = parseArgs([
            "-m",
            "-a", "edit",
            "-p", "testuser",
            "-f", f"{TEST_IMAGE_DIR}/test_face.jpg"
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 7

    # Checks failed edit action on broken combination rules lock/unlock gesture file
    def test_user_gesture_rule_broken_fail_on_edit(self):
        args = parseArgs([
            "-m",
            "-a", "edit",
            "-p", "testuser",
            "-u", f"{TEST_IMAGE_DIR}/test_unlock_1.jpg {TEST_IMAGE_DIR}/test_unlock_2.jpg {TEST_IMAGE_DIR}/test_unlock_3.jpg {TEST_IMAGE_DIR}/test_unlock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 20

        args = parseArgs([
            "-m",
            "-a", "edit",
            "-p", "testuser",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 21

        args = parseArgs([
            "-m",
            "-a", "edit",
            "-p", "testuser",
            "-l", f"{TEST_IMAGE_DIR}/test_lock_1.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_4.jpg".split(),
            "-u", f"{TEST_IMAGE_DIR}/test_lock_4.jpg {TEST_IMAGE_DIR}/test_lock_3.jpg {TEST_IMAGE_DIR}/test_lock_2.jpg {TEST_IMAGE_DIR}/test_lock_1.jpg".split()
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 22


class TestManagerDelete:
    # Checks a test username ommited fails
    def test_user_delete_username_omitted_fail(self):
        args = parseArgs([
            "-m",
            "-a", "delete"
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 13

    # Checks a test user doesn't exist fails
    def test_user_delete_user_not_exist_fail(self):
        args = parseArgs([
            "-m",
            "-a", "delete",
            "-p", "foobar"
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 13

    # Checks a test user delete succeeds
    def test_user_delete_user_succeeds(self):
        args = parseArgs([
            "-m",
            "-a", "delete",
            "-p", "testuser"
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 0

    # Checks the user just deleted was actually deleted
    def test_user_delete_user_succeeded(self):
        args = parseArgs([
            "-m",
            "-a", "delete",
            "-p", "testuser"
        ])
        with pytest.raises(SystemExit):
            main(args)
        assert readResponseFile().CODE == 9


# After running tests, shutdown project
# @pytest.fixture(scope="session")
def teardown_module(__name__):
    logging.getLogger().info("[INFO] All tests completed, shutting down rekog project...")
    with pytest.raises(SystemExit):
        projectHandler(False)
