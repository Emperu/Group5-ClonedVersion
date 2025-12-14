import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


class ll_ATS(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()

    def test_ll(self):

        driver = self.driver
        driver.maximize_window()
        user = "87654321"
        pwd = "password123"
        driver.get("http://127.0.0.1:8000/login")
        time.sleep(4)
        elem = driver.find_element(By.ID,"role")
        elem.send_keys('tutor')
        elem = driver.find_element(By.ID,"NUID")
        elem.send_keys(user)
        elem = driver.find_element(By.ID,"password")
        elem.send_keys(pwd)
        time.sleep(3)
        elem.send_keys(Keys.RETURN)
        driver.get("http://127.0.0.1:8000")
        time.sleep(3)

        # find 'Appointments' in navbar and click it – all one Python statement
        elem = driver.find_element(By.XPATH, "//a[contains(., 'Appointments')]")
        elem.send_keys(Keys.RETURN)
        time.sleep(5)

        try:
            # verify Tutor Appointments page exists after clicking "Appointments"
            # note that this test requires at least one appointment in the database to be successful
            heading = driver.find_element(By.TAG_NAME, "h1")
            self.driver.close()
            assert True

        except NoSuchElementException:
            driver.close()
            self.fail("Tutor Appointments page does not appear when 'Appointments' is clicked")

        time.sleep(2)

    def tearDown(self):
        self.driver.quit()


if __name__ == "__main__":
    unittest.main()