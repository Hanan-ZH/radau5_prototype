#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 17 15:50:07 2018

@author: H.Hamamera
"""

"""
Implicit Runge-Kutta method:
The scheme is Radua 2A of order 2s-1 using S=2 and p=3. This method is of order 5.
* It solves the differential equation dy/dt= f(y, t) using implicit Runge-Kutta method of fifth order.
* Define all constant matricies and time step h.
* Construct small matricies(T_inverse*I, T*I, -h_inverse(B*I) ) where * is the tensor product.
* Define a functions that calculate both the right and the left sides of the linear system Ax=B.
* iterate to solve for delta_W.
* In the outer for loop, find psi(tn).
* Save results in lists and plot the exact solution vs. the approximate one.
"""

# import libraries
import numpy as np
import math as m
import matplotlib.pyplot as plt
from scipy import linalg as LA
import matplotlib.ticker as ticker
from matplotlib.ticker import AutoMinorLocator

# define w0, w1, w, omega, N and time
# *************** Change parameters here *****************************
w0, w1, w, integration_time, N = 10.0, 5.0, 15.0, 1, 100
# ******************************************************************** 

omega= m.sqrt(w1**2+ (w0-0.5*w)**2)
step= (2*m.pi)/(N*max(w, omega))
time= int(integration_time/step)

# save time tn in a list:
def time_division(time, step):
    tn= 0
    for i in range(0, time):
        tn= tn+step
        yield tn
    
"""
Define all the matricies and time step h.
"""
A = np.matrix([[(88-7*np.sqrt(6))/360, (296-169*np.sqrt (6))/1800, (-2+3* np.sqrt (6))/225],
               [(296+169* np.sqrt (6))/1800, (88+7* np.sqrt (6))/360, (-2-3* np.sqrt (6))/225],
               [(16- np.sqrt (6))/36, (16+ np.sqrt (6))/36, (1/9.0)]])

A_inverse= np.matrix([[ 3.22474487,  1.16784008, -0.25319726],
                     [-3.56784008,  0.77525513,  1.05319726],
                     [ 5.53197265, -7.53197265,  5.0        ]])

T= np.matrix([[0.12845806,    0.02730865, 0.09123239 ],
              [-0.18563595,  -0.3482489,  0.24171793 ],
              [-0.90940352,    0.0,       0.96604818 ]])

B= np.matrix([[2.68108287,-3.0504302, 0.0 ],
             [3.0504302, 2.68108287, 0.0 ],
             [0.0, 0.0, 3.63783425]])

T_inverse= np.matrix([[ 4.59501051,  0.36032715, -0.52410567],
                     [ 0.55296977, -2.82814717,  0.65541775],
                     [ 4.32558005,  0.33919921,  0.54177056]])


"""
The small matricies are named such that: - h_inverse * T_inverse( B * I ) = M1 ;
                                         T_inverse * I = M2T * I = M3
"""

# define the identity matricies for n=2 and s=3:
def identity(n):
    return [[1 if i==j else 0 for j in range(n)] for i in range(n)]

# define small matricies:
h= step
M1= (-1/h)*np.kron(B, identity(2))
M2= np.kron(T_inverse, identity(2))
M3= np.kron(T, identity(2))

# get di from bi and define ci:
b= np.matrix([(16.0-np.sqrt(6.0))/36.0, (16.0+np.sqrt(6.0))/36.0, 1.0/9.0])
d= b*A_inverse
d1= d.item(0)
d2= d.item(1)
d3= d.item(2)
c1, c2, c3= (4.0-np.sqrt(6.0))/10.0, (4.0+np.sqrt(6.0))/10.0, 1.0
c_avg= (c1+c2+c3)/3

# set relation between z_k and w_k:
def Z_k(W_k):
    z_k= M3*W_k
    return z_k

# define the Hamiltonian H(t) as a function to be called later in the loop:
def Hamiltonian(w0, w1, w, tn):
    H= np.matrix([[w0, w1*np.exp(-1j*w*tn)], [w1*np.exp(1j*w*tn), -w0]])
    return H

# define the function f(W_k) that calculates the right side of the linear system:
def F(W_k1, W_k2, W_k3, tn, Yn):  # be careful to input W_ki as kets not bras, ie. use transposed matrices
    h= step
    W_k= np.vstack((W_k1, W_k2, W_k3))
    W_k_trans= Z_k(W_k)
    W_k1_trans= (np.matrix([W_k_trans.item(0), W_k_trans.item(1)])).T
    W_k2_trans= (np.matrix([W_k_trans.item(2), W_k_trans.item(3)])).T
    W_k3_trans= (np.matrix([W_k_trans.item(4), W_k_trans.item(5)])).T 
    Q1= -1j*Hamiltonian(w0, w1, w, tn+h*c1)*(W_k1_trans+Yn)
    Q2= -1j*Hamiltonian(w0, w1, w, tn+h*c2)*(W_k2_trans+Yn)
    Q3= -1j*Hamiltonian(w0, w1, w, tn+h*c3)*(W_k3_trans+Yn)
    F= np.vstack((Q1, Q2, Q3)) 
    F= M1*W_k+ M2* F
    return np.array(F)

"""
Solve for deltaW_k then set W_k equal to W_k + deltaW_k, do k iterations until convergence.
- tn will be in the outer loop
- define the left side of the linear system, in our problem the jacobian
  is just the hamiltonian H multiplyed by -1j and is constant 
- for all iterations k: the jacobian will change with changing the time tn(simplified Newton method)
- We have two matricies to construct on the left, first is for the n dimensional subsystem(A_n) and the second is 
  for the real 2n dimensional system(A_2n) which is then transformed into the complex n dimensional (A_n_complex)
- the eigenvalues used in the construction of A matricies are the products of (1/h) with the eigenvalues of A_inverse

"""
def A_3n(h, tn):
    A1= np.kron(B, identity(2))
    A2= np.kron(identity(3), -1j*Hamiltonian(w0, w1, w, tn))
    A3= (1/h)*A1- A2
    
    return np.array(A3)


def PSI(h, time):
    tn=0
    Yn= (np.matrix([0, 1])).T
    
    for i in range(0, time):
        W_k= (np.matrix([0.0,0.0,0.0,0.0,0.0,0.0])).T
        W_k1= (np.matrix([W_k.item(0),W_k.item(1)])).T
        W_k2= (np.matrix([W_k.item(2),W_k.item(3)])).T
        W_k3= (np.matrix([W_k.item(4),W_k.item(5)])).T
        k= 0
        error= 1.0
        while error >= 0.01: 
              deltaW_k= np.linalg.solve(A_3n(h, tn),F(W_k1, W_k2, W_k3, tn, Yn))
              delta1W_k= (np.matrix([deltaW_k.item(0),deltaW_k.item(1)])).T
              delta2W_k= (np.matrix([deltaW_k.item(2),deltaW_k.item(3)])).T
              delta3W_k= (np.matrix([deltaW_k.item(4),deltaW_k.item(5)])).T
              
              deltaW_k= np.vstack((delta1W_k, delta2W_k,delta3W_k))
              deltaZ_k_old= Z_k(W_k)#to get deltaZ(k-1)
              
              W_k= W_k+ deltaW_k #update W_k 
              W_k1= (np.matrix([W_k.item(0), W_k.item(1)])).T
              W_k2= (np.matrix([W_k.item(2), W_k.item(3)])).T
              W_k3= (np.matrix([W_k.item(4), W_k.item(5)])).T
              deltaZ_k_new= Z_k(W_k)# to get deltaZ(k)
              
              if k>= 1:
                 norm_k_old= LA.norm(deltaZ_k_old)
                 norm_k_new= LA.norm(deltaZ_k_new)
                 theta_k= norm_k_new/norm_k_old
                 if theta_k== 1.0:
                    error= 0.0
                 else:
                     eta_k= theta_k/(1.0-theta_k)
                     tol= abs(norm_k_new - norm_k_old)/min(norm_k_new, norm_k_old)
                     error= eta_k*norm_k_new/tol
              else:
                  error= 1.0
              k= k+1
        
        Z_k1= (np.matrix([ deltaZ_k_new.item(0),  deltaZ_k_new.item(1)])).T
        Z_k2= (np.matrix([ deltaZ_k_new.item(2),  deltaZ_k_new.item(3)])).T
        Z_k3= (np.matrix([ deltaZ_k_new.item(4), deltaZ_k_new.item(5)])).T 
        Yn= Yn+ d1*Z_k1 + d2*Z_k2 + d3*Z_k3
        tn= tn+step
        
        yield Yn

        
#save psi data in a list           
PSI_Matrix= list(PSI(step, time))
    
# find the expectation value of the spin matrix for x, y and z-components       
def x_spin(time):
    for i in range(0, time):
        psi_tn= PSI_Matrix[i]
        sigma_x= np.matrix([[0, 1], [1, 0]])
        psi_dagger= psi_tn.H
        spin_x= psi_dagger*sigma_x*psi_tn
        spin_x= spin_x.item(0)
        yield spin_x

def y_spin(time):
    for i in range(0, time):
        psi_tn= PSI_Matrix[i]
        sigma_y= np.matrix([[0, -1j], [1j, 0]])
        psi_dagger= psi_tn.H
        spin_y= psi_dagger*sigma_y*psi_tn
        spin_y= spin_y.item(0)
        yield spin_y

def z_spin(time):
    for i in range(0, time):
        psi_tn= PSI_Matrix[i]
        sigma_z= np.matrix([[1, 0], [0, -1]])
        psi_dagger= psi_tn.H
        spin_z= psi_dagger*sigma_z*psi_tn
        spin_z= spin_z.item(0)
        yield spin_z  

#def solution in tetrms of (w0, w1, w, omega, time):
#define exact x, y and z-components in terms of (w,w0.w1 and omega)  
def x_exact_comp(w0, w1, w, omega):
    for i in range(0, time):
        t= i*step
        xe= (1-m.cos(2*omega*t))*m.cos(w*t)*(w0-0.5*w)/omega
        xe= xe+ m.sin(w*t)*m.sin(2*omega*t)
        xe= xe*(-w1/omega)
        yield xe 
            
def y_exact_comp(w0, w1, w, omega):
    for i in range(0, time):
        t= i*step      
        ye= (1-m.cos(2*omega*t))*m.sin(w*t)*(w0-0.5*w)/omega
        ye= ye- m.cos(w*t)*m.sin(2*omega*t)
        ye= ye*(-w1/omega)
        yield ye
           
def z_exact_comp(w0, w1, w, omega):
    for i in range(0, time):
        t= i*step
        ze= (w0-0.5*w)**2-w1**2
        ze= ze/((w0-0.5*w)**2+w1**2)
        ze= ze*(m.sin(omega*t))**2
        ze= -1*(ze+(m.cos(omega*t))**2)
        yield ze
                
#save data in lists      
time_steps_data= list(time_division(time, step))
spin_x_data= list(x_spin(time))
spin_y_data= list(y_spin(time))
spin_z_data= list(z_spin(time))

#remove imaginary part (0j) from all lists for plotting
spin_x_data_noj= np.array(spin_x_data).real
spin_y_data_noj= np.array(spin_y_data).real
spin_z_data_noj= np.array(spin_z_data).real

#save exact data in lists for plotting       
x_exact_data= list(x_exact_comp(w0, w1, w, omega))
y_exact_data= list(y_exact_comp(w0, w1, w, omega))
z_exact_data= list(z_exact_comp(w0, w1, w, omega))

#Average error:
Size_spin= len(x_exact_data)
sum_difference_x= 0.0
sum_difference_y= 0.0
sum_difference_z= 0.0

for i in range(0, time):
    difference_x= np.absolute(x_exact_data[i]- spin_x_data_noj[i])
    sum_difference_x= difference_x + sum_difference_x
    difference_y= np.absolute(y_exact_data[i]- spin_y_data_noj[i])
    sum_difference_y= difference_y + sum_difference_y
    difference_z= np.absolute(z_exact_data[i]- spin_z_data_noj[i])
    sum_difference_z= difference_z + sum_difference_z

error_x= sum_difference_x/ Size_spin
error_y= sum_difference_y/ Size_spin
error_z= sum_difference_z/ Size_spin


# Three subplots sharing both x/y axes
f, (ax1, ax2, ax3) = plt.subplots(3,figsize=(10.8,8.0), sharex=True, sharey=True)
# Title
plt.suptitle(r' Exact vs. numerically predicted Magnetic-state omponents in arbitrary time  ')
#plot for x-component, exact, numerical
ax1.plot(time_steps_data, x_exact_data, label='Exact' )
ax1.plot(time_steps_data, spin_x_data_noj, label='Num')
#plot for y-component
ax2.plot(time_steps_data, y_exact_data, label='Exact')
ax2.plot(time_steps_data, spin_y_data_noj, label='Num')
#plot for z-component
ax3.plot(time_steps_data, z_exact_data, label='Exact')
ax3.plot(time_steps_data, spin_z_data_noj, label='Num')
#set lables
ax1.set_ylabel(r'M$_x$' , family="serif", fontsize=18)
ax2.set_ylabel(r'M$_y$' , family="serif", fontsize=18)
ax3.set_ylabel(r'M$_z$' , family="serif", fontsize=18)
# Fine-tune figure; make subplots close to each other and hide x ticks for all but bottom plot.
f.subplots_adjust(hspace=0)

ax1.xaxis.set_major_locator(ticker.MultipleLocator(0.1))
ax1.xaxis.set_minor_locator(AutoMinorLocator(0.1))

ax1.tick_params(axis='both',which='major', direction="in", top="off", right="on", bottom="on", length=4, labelsize=14)
ax2.tick_params(axis='both',which='major', direction="in", top="off", right="on", bottom="on", length=4, labelsize=14)
ax3.tick_params(axis='both',which='major', direction="in", top="off", right="on", bottom="on", length=4, labelsize=14)

ax1.patch.set_edgecolor('black')  
ax1.patch.set_linewidth('1.2')
ax2.patch.set_edgecolor('black')  
ax2.patch.set_linewidth('1.2')
ax3.patch.set_edgecolor('black')  
ax3.patch.set_linewidth('1.2')

ax3.set_xlabel('Time (a.u.)', family="serif", fontsize=18)

#plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)
plt.legend()
plt.show()
