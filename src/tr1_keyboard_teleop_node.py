#!/usr/bin/env python
from __future__ import print_function
import rospy, sys, tty, termios, time, yaml
from std_msgs.msg import Float64
from sensor_msgs.msg import JointState

pubs = []
pubs.append(rospy.Publisher('/tr1/controller/effort/JointRightShoulderPan/command', Float64, queue_size=10))
pubs.append(rospy.Publisher('/tr1/controller/effort/JointRightShoulderTilt/command', Float64, queue_size=10))
pubs.append(rospy.Publisher('/tr1/controller/effort/JointRightUpperArmRoll/command', Float64, queue_size=10))
pubs.append(rospy.Publisher('/tr1/controller/effort/JointRightElbowFlex/command', Float64, queue_size=10))
pubs.append(rospy.Publisher('/tr1/controller/effort/JointRightForearmRoll/command', Float64, queue_size=10))
pubs.append(rospy.Publisher('/tr1/controller/effort/JointRightWristFlex/command', Float64, queue_size=10))
pubs.append(rospy.Publisher('/tr1/controller/effort/JointRightWristRoll/command', Float64, queue_size=10))
pubs.append(rospy.Publisher('/tr1/controller/effort/JointRightGripper/command', Float64, queue_size=10))

selectedPubIndex = 0
joint_states = {}
joint_offsets = " "

def upPubIndex():
	global selectedPubIndex
	if (selectedPubIndex + 1 >= len(pubs)):
		selectedPubIndex = 0
	else:
		selectedPubIndex += 1

def downPubIndex():
	global selectedPubIndex
	if (selectedPubIndex <= 0):
		selectedPubIndex = len(pubs) - 1
	else:
		selectedPubIndex -= 1

def jointStateCallback(data):
	global joint_states
	joint_states = data

def calibrate():
	global joint_offsets
	jointOffsetsPath = rospy.get_param("/joint_offsets_path")
	with open(jointOffsetsPath, 'r') as stream:
		try:
			joint_offsets = yaml.load(stream)
			for idx, val in enumerate(joint_states.name):
				joint_offsets["tr1"]["joint_offsets"][val] = (joint_states.position[idx] * -1)

			#joint_offsets["tr1"]["joint_offsets"]["JointRightShoulderTilt"] += 1.5707963
		except yaml.YAMLError as exc:
			print (exc)

	with open(jointOffsetsPath, 'w') as stream:
		try:
			yaml.dump(joint_offsets, stream, default_flow_style=False)
			print("joint_offsets.yaml successfully written over and TR1 successfully calibrated")
		except yaml.YAMLError as exc:
			print (exc)

def keyChange(key):
	key = str(key)
	if key == 'w':
		upPubIndex()
	elif key == 's':
		downPubIndex()
	elif key == 'a':
		pubs[selectedPubIndex].publish(-1)
	elif key == 'd':
		pubs[selectedPubIndex].publish(1)

if __name__ == '__main__':
	rospy.init_node('tr1_keyboard_teleop', anonymous=True)
	rospy.Subscriber("/joint_states", JointState, jointStateCallback)
	#rospy.spin()

	time.sleep(3)
	
	msg = """Welcome!
Select your joint using the 'w' and 's' keys
Actuate using the 'a' and 'd' keys
Press 'esc' to exit program\n"""

	print(msg)

	orig_settings = termios.tcgetattr(sys.stdin)
	tty.setraw(sys.stdin)

	try:	
		x = 0
		sameKeyCount = 0
		while x != chr(27): # ESC
			_x = sys.stdin.read(1)[0]
			if str(_x) == 'c':
				calibrate()
			elif str(_x) == 'w':
				upPubIndex()
			elif str(_x) == 's':
				downPubIndex()
			else:
				if (_x != x):
					keyChange(_x)
					sameKeyCount = 1
				else:
					sameKeyCount += 1
					if (sameKeyCount % 2 == 0):
						pubs[selectedPubIndex].publish(0)
					else:
						keyChange(_x)
			x = _x
			jointName = "(" + str(selectedPubIndex + 1) + ") " + pubs[selectedPubIndex].name.replace("/tr1/controller/effort/","").replace("/command","")
			print("\rSelected Joint: " + jointName + "; Key pressed " + str(x), end="                   ")
	except Exception, e:
		print("Error occured: " + str(e))
	finally:
		termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)
