#!/usr/bin/python
# -*- coding: utf-8 -*-
import smbus            # use I2C
import math
from time import sleep  # time module
import csv
import dtw
import numpy as np
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw
from matplotlib import pyplot as plt
import pandas as pd

### define #############################################################
DEV_ADDR = 0x68         # device address
PWR_MGMT_1 = 0x6b       # Power Management 1
ACCEL_XOUT = 0x3b       # Axel X-axis
ACCEL_YOUT = 0x3d       # Axel Y-axis
ACCEL_ZOUT = 0x3f       # Axel Z-axis
TEMP_OUT = 0x41         # Temperature
GYRO_XOUT = 0x43        # Gyro X-axis
GYRO_YOUT = 0x45        # Gyro Y-axis
GYRO_ZOUT = 0x47        # Gyro Z-axis

# Pickの学習用データを定義
train_data_set_ax = pd.read_csv('pick_train_data_2/pick_accel_x.csv', usecols=[2]).values.reshape(-1, 1)
train_data_set_ay = pd.read_csv('pick_train_data_2/pick_accel_y.csv', usecols=[2]).values.reshape(-1, 1)
train_data_set_az = pd.read_csv('pick_train_data_2/pick_accel_z.csv', usecols=[2]).values.reshape(-1, 1)
train_data_set_gx = pd.read_csv('pick_train_data_2/pick_gyro_x.csv', usecols=[0]).values.reshape(-1, 1)

train_data_set_gy = pd.read_csv('pick_train_data_2/pick_gyro_y.csv', usecols=[0]).values.reshape(-1, 1)
train_data_set_gx_2 = pd.read_csv('pick_train_data_2/pick_gyro_x.csv', usecols=[1]).values.reshape(-1, 1)
train_data_set_gy_2 = pd.read_csv('pick_train_data_2/pick_gyro_y.csv', usecols=[1]).values.reshape(-1, 1)
train_data_set_gx_3 = pd.read_csv('pick_train_data_2/pick_gyro_x.csv', usecols=[2]).values.reshape(-1, 1)
train_data_set_gy_3 = pd.read_csv('pick_train_data_2/pick_gyro_y.csv', usecols=[2]).values.reshape(-1, 1)
train_data_set_gx_4 = pd.read_csv('pick_train_data_2/pick_gyro_x.csv', usecols=[3]).values.reshape(-1, 1)
train_data_set_gy_4 = pd.read_csv('pick_train_data_2/pick_gyro_y.csv', usecols=[3]).values.reshape(-1, 1)
train_data_set_gx_5 = pd.read_csv('pick_train_data_2/pick_gyro_x.csv', usecols=[4]).values.reshape(-1, 1)
train_data_set_gy_5 = pd.read_csv('pick_train_data_2/pick_gyro_y.csv', usecols=[4]).values.reshape(-1, 1)


# Dropの学習用データを定義
drop_train_data_set_ax = pd.read_csv('drop_train_data/drop_accel_x.csv', usecols=[0]).values.reshape(-1, 1)
drop_train_data_set_ay = pd.read_csv('drop_train_data/drop_accel_y.csv', usecols=[0]).values.reshape(-1, 1)
drop_train_data_set_az = pd.read_csv('drop_train_data/drop_accel_z.csv', usecols=[0]).values.reshape(-1, 1)
drop_train_data_set_gx = pd.read_csv('drop_train_data/drop_gyro_x.csv', usecols=[0]).values.reshape(-1, 1)
drop_train_data_set_gx_2 = pd.read_csv('drop_train_data/drop_gyro_x.csv', usecols=[1]).values.reshape(-1, 1)
drop_train_data_set_gx_3 = pd.read_csv('drop_train_data/drop_gyro_x.csv', usecols=[2]).values.reshape(-1, 1)
drop_train_data_set_gx_4 = pd.read_csv('drop_train_data/drop_gyro_x.csv', usecols=[3]).values.reshape(-1, 1)
drop_train_data_set_gx_5 = pd.read_csv('drop_train_data/drop_gyro_x.csv', usecols=[4]).values.reshape(-1, 1)

drop_train_data_set_gy = pd.read_csv('drop_train_data/drop_gyro_x.csv', usecols=[0]).values.reshape(-1, 1)
drop_train_data_set_gy_2 = pd.read_csv('drop_train_data/drop_gyro_x.csv', usecols=[1]).values.reshape(-1, 1)
drop_train_data_set_gy_3 = pd.read_csv('drop_train_data/drop_gyro_x.csv', usecols=[2]).values.reshape(-1, 1)
drop_train_data_set_gy_4 = pd.read_csv('drop_train_data/drop_gyro_x.csv', usecols=[3]).values.reshape(-1, 1)
drop_train_data_set_gy_5 = pd.read_csv('drop_train_data/drop_gyro_x.csv', usecols=[4]).values.reshape(-1, 1)


# テストデータを作成するための初期データを作成
test_data_set_ax = np.arange(60).reshape(-1, 1)
test_data_set_ay = np.arange(60).reshape(-1, 1)
test_data_set_az = np.arange(60).reshape(-1, 1)
test_data_set_gx = np.arange(60).reshape(-1, 1)
test_data_set_gy = np.arange(60).reshape(-1, 1)

pick_dtw_gx_list = []
pick_dtw_gy_list = []
drop_dtw_gx_list = []
drop_dtw_gy_list = []

"""
データ数120個の枠内に新しいデータを挿入し不要なデータをドロップさせる
* 枠内のデータ数は考える必要あり

@param 観測データセット
@param 観測データ

@return 生成した観測データセット
"""
def remake_test_data_set(test_data_set, data):
    new_data = np.insert(test_data_set, 60, data, axis=0)
    new_data = np.delete(new_data, 0, 0)
    return new_data

# 1byte read
def read_byte( addr ):
    return bus.read_byte_data( DEV_ADDR, addr )
 
# 2byte read
def read_word( addr ):
    high = read_byte( addr   )
    low  = read_byte( addr+1 )
    return (high << 8) + low
 
# Sensor data read
def read_word_sensor( addr ):
    val = read_word( addr )
    if( val < 0x8000 ):
        return val # positive value
    else:
        return val - 65536 # negative value
 
# Get Temperature
def get_temp():
    temp = read_word_sensor( TEMP_OUT )
    # offset = -521 @ 35℃
    return ( temp + 521 ) / 340.0 + 35.0
 
# Get Gyro data (raw value)
def get_gyro_data_lsb():
    x = read_word_sensor( GYRO_XOUT )
    y = read_word_sensor( GYRO_YOUT )
    z = read_word_sensor( GYRO_ZOUT )
    return [ x, y, z ]
# Get Gyro data (deg/s)
def get_gyro_data_deg():
    x,y,z = get_gyro_data_lsb()
    # Sensitivity = 131 LSB/(deg/s), @cf datasheet
    x = x / 131.0
    y = y / 131.0
    z = z / 131.0
    return [ x, y, z ]
 
# Get Axel data (raw value)
def get_accel_data_lsb():
    x = read_word_sensor( ACCEL_XOUT )
    y = read_word_sensor( ACCEL_YOUT )
    z = read_word_sensor( ACCEL_ZOUT )
    return [ x, y, z ]
# Get Axel data (G)
def get_accel_data_g():
    x,y,z = get_accel_data_lsb()
    # Sensitivity = 16384 LSB/G, @cf datasheet
    x = x / 16384.0
    y = y / 16384.0
    z = z / 16384.0
    return [x, y, z]

def insert_csv(gyro_x, gyro_y, gyro_z, accel_x, accel_y, accel_z):
    with open('sample.csv', 'a') as csvfile:
        writer = csv.writer(csvfile, lineterminator='\n')
        writer.writerow([gyro_x, gyro_y, gyro_z, accel_x, accel_y, accel_z])
### Main function ######################################################
bus = smbus.SMBus( 1 )
bus.write_byte_data( DEV_ADDR, PWR_MGMT_1, 0 )

"""
pick動作を検出する

@param 加速度、各加速度を用いたDTWの値
"""
def check_pick_motion(dtw_ax_result, dtw_ay_result, dtw_az_result, dtw_gx_result, dtw_gy_result):
    if 0.75 < accel_z and dtw_gx_result < 100000 and dtw_gy_result < 2000000:
        print ('pick')
        return 'pick'

"""
Drop動作を検出する
@param 加速度、各加速度を用いたDTWの値
"""
def check_drop_motion(drop_dtw_ax_result, drop_dtw_ay_result, drop_dtw_az_result, drop_dtw_gx_result, drop_dtw_gy_result):
    if 0.75 < accel_z and  drop_dtw_gx_result < 400000 and drop_dtw_gy_result < 2000000:
        print('drop')
        return 'drop'
"""
観測データを出力する
"""
def print_sencing_data():
    temp = get_temp()
    print 't= %.2f' % temp, '\t',

    gyro_x,gyro_y,gyro_z = get_gyro_data_deg()
    print 'Gx= %.3f' % gyro_x, '\t',
    print 'Gy= %.3f' % gyro_y, '\t',
    print 'Gz= %.3f' % gyro_z, '\t',

    accel_x,accel_y,accel_z = get_accel_data_g()
    print 'Ax= %.3f' % accel_x, '\t',
    print 'Ay= %.3f' % accel_y, '\t',
    print 'Az= %.3f' % accel_z, '\t',
    print # 改行

def print_pick_dtw_result(ax, ay, az, gx, gy):
    print('-----------------------pick dtw result-------------------------------')
    print(ax)
    print(ay)
    print(az)
    print(gx)
    print(gy)
    print('--------------------------------end-----------------------------------')

def print_drop_dtw_result(ax, ay, az, gx, gy):
    print('-----------------------drop dtw result--------------------------------')
    print(ax)
    print(ay)
    print(az)
    print(gx)
    print(gy)
    print('--------------------------------end------------------------------------')

def check_pick_or_drop(pick_diw_x, pick_dtw_y, drop_dtw_x, drop_dtw_y):
    if pick_diw_x < drop_dtw_x and pick_dtw_y < drop_dtw_y:
        return 'pick'
    elif pick_diw_x > drop_dtw_x and pick_dtw_y > drop_dtw_y:
        return 'drop'



count = 0
drop_count = 0
tt = 0
while 1:
#    print_sencing_data()
#    print 'csvファイル書き込み'
    #insert_csv(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)

    # 加速度を取得
    accel_x, accel_y, accel_z = get_accel_data_g()
    # 角加速度を取得
    gyro_x, gyro_y, gyro_z = get_gyro_data_deg()
    
    # 枠内にデータを作成する
    test_data_set_ax = remake_test_data_set(test_data_set_ax, accel_x)
    test_data_set_ay = remake_test_data_set(test_data_set_ay, accel_y)
    test_data_set_az = remake_test_data_set(test_data_set_az, accel_z)
    test_data_set_gx = remake_test_data_set(test_data_set_gx, gyro_x)
    test_data_set_gy = remake_test_data_set(test_data_set_gy, gyro_y)

#    print (len(test_data_set))
    
    # pickのDTWの値を取得する
    pick_dtw_ax_result = dtw.getDTW(train_data_set_ax, test_data_set_ax)
    pick_dtw_ay_result = dtw.getDTW(train_data_set_ay, test_data_set_ay)
    pick_dtw_az_result = dtw.getDTW(train_data_set_az, test_data_set_az)
    pick_dtw_gx_result = dtw.getDTW(train_data_set_gx, test_data_set_gx)
    pick_dtw_gy_result = dtw.getDTW(train_data_set_gy, test_data_set_gy)
    pick_dtw_gx_result_1 = dtw.getDTW(train_data_set_gx_2, test_data_set_gx)
    pick_dtw_gy_result_1 = dtw.getDTW(train_data_set_gy_2, test_data_set_gy)
    pick_dtw_gx_result_2 = dtw.getDTW(train_data_set_gx_3, test_data_set_gx)
    pick_dtw_gy_result_2 = dtw.getDTW(train_data_set_gy_3, test_data_set_gy)
    pick_dtw_gx_result_3 = dtw.getDTW(train_data_set_gx_4, test_data_set_gx)
    pick_dtw_gy_result_3 = dtw.getDTW(train_data_set_gy_4, test_data_set_gy)
    pick_dtw_gx_result_4 = dtw.getDTW(train_data_set_gx_5, test_data_set_gx)
    pick_dtw_gy_result_4 = dtw.getDTW(train_data_set_gy_5, test_data_set_gy)

    pick_dtw_gx_list.extend([pick_dtw_gx_result, pick_dtw_gx_result_1, pick_dtw_gx_result_2, pick_dtw_gx_result_3, pick_dtw_gx_result_4])
    pick_dtw_gy_list.extend([pick_dtw_gy_result, pick_dtw_gy_result_1, pick_dtw_gy_result_2, pick_dtw_gy_result_3, pick_dtw_gy_result_4])
    pick_dtw_gx_result = min(pick_dtw_gx_list) ** 2     

    # DroｐのDTW値を算出
    drop_dtw_ax_result = dtw.getDTW(drop_train_data_set_ax, test_data_set_ax)
    drop_dtw_ay_result = dtw.getDTW(drop_train_data_set_ay, test_data_set_ay)
    drop_dtw_az_result = dtw.getDTW(drop_train_data_set_az, test_data_set_az)

    drop_dtw_gx_result = dtw.getDTW(drop_train_data_set_gx, test_data_set_gx)
    drop_dtw_gy_result = dtw.getDTW(drop_train_data_set_gy, test_data_set_gy)
    drop_dtw_gx_result_1 = dtw.getDTW(drop_train_data_set_gx_2, test_data_set_gx)
    drop_dtw_gy_result_1 = dtw.getDTW(drop_train_data_set_gy_2, test_data_set_gy)
    drop_dtw_gx_result_2 = dtw.getDTW(drop_train_data_set_gx_3, test_data_set_gx)
    drop_dtw_gy_result_2 = dtw.getDTW(drop_train_data_set_gy_3, test_data_set_gy)
    drop_dtw_gx_result_3 = dtw.getDTW(drop_train_data_set_gx_4, test_data_set_gx)
    drop_dtw_gy_result_3 = dtw.getDTW(drop_train_data_set_gy_4, test_data_set_gy)
    drop_dtw_gx_result_4 = dtw.getDTW(drop_train_data_set_gx_5, test_data_set_gx)
    drop_dtw_gy_result_4 = dtw.getDTW(drop_train_data_set_gy_5, test_data_set_gy)

    drop_dtw_gx_list.extend([drop_dtw_gx_result, drop_dtw_gx_result_1, drop_dtw_gx_result_2, drop_dtw_gx_result_3, drop_dtw_gx_result_4])
    drop_dtw_gy_list.extend([drop_dtw_gy_result, drop_dtw_gy_result_1, drop_dtw_gy_result_2, drop_dtw_gy_result_3, drop_dtw_gy_result_4])
    drop_dtw_gx_result = min(drop_dtw_gx_list) ** 2
    drop_dtw_gy_result = min(drop_dtw_gy_list) ** 2
    if 7.5 < accel_z < 12.5:
        sec = time.time()
        print(sec)
        print (accel_z)
        if sec > 2:
            print(check_pick_or_drop(pick_dtw_gx_result, pick_dtw_gy_result, drop_dtw_gx_result, drop_dtw_gy_result))

            

  
    #print_sencing_data()
    #print_pick_dtw_result(pick_dtw_ax_result, pick_dtw_ay_result, pick_dtw_az_result, pick_dtw_gx_result, pick_dtw_gy_result)
    #print_pick_dtw_result(pick_dtw_gx_result, pick_dtw_gx_result_1, pick_dtw_gx_result_2, pick_dtw_gx_result_3, pick_dtw_gx_result_4)
    #print_drop_dtw_result(drop_dtw_ax_result, drop_dtw_ay_result, drop_dtw_az_result, drop_dtw_gx_result, drop_dtw_gy_result)
    #print_drop_dtw_result(pick_dtw_gy_result, pick_dtw_gy_result_1, pick_dtw_gy_result_2, pick_dtw_gy_result_3, pick_dtw_gy_result_4)
    pick_dtw_gx_list = []
    pick_dtw_gy_list = []
    drop_dtw_gx_list = []
    drop_dtw_gy_list = []
    tt += 1
