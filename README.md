# Voluntary-Motion
fish_serial.py is a Python 3 code to display a voluntary motion paradigm. Uses image-files found in the zipped folder "images". Records force while subject presses on the foot pedal (built by Francesco Santini and Xeni Deligianni) and display the applied force overlaid on the predefined force surve in real time. It needs pygamezero package. Before running the code, check COM port. To start, 
run fisch_serial.py in Python. Reading and logging of serial port starts with run => LogFile_data_time.
After start: type amplitude of force that you expect or aim at.
Press <- to pause fish and bubbles and logging of trigger.
Press -> to start fish and bubbles and logging of trigger.
Press arrow up to redraw bubbles.
Press t to send reset_tare signal to green box.
Press m or p to change force amplitude.
