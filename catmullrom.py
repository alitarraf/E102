import numpy
import pylab as plt

def CatmullRomSpline(P0, P1, P2, P3, nPoints=100):
  """
  P0, P1, P2, and P3 should be (x,y) point pairs that define the Catmull-Rom spline.
  nPoints is the number of points to include in this curve segment.
  """
  # Convert the points to numpy so that we can do array multiplication
  P0, P1, P2, P3 = map(numpy.array, [P0, P1, P2, P3])

  # Calculate t0 to t4
  alpha = 0.5
  def tj(ti, Pi, Pj):
    xi, yi = Pi
    xj, yj = Pj
    return ( ( (xj-xi)**2 + (yj-yi)**2 )**0.5 )**alpha + ti

  t0 = 0
  t1 = tj(t0, P0, P1)
  t2 = tj(t1, P1, P2)
  t3 = tj(t2, P2, P3)

  # Only calculate points between P1 and P2
  t = numpy.linspace(t1,t2,nPoints)

  # Reshape so that we can multiply by the points P0 to P3
  # and get a point for each value of t.
  t = t.reshape(len(t),1)
  #print(t)
  A1 = (t1-t)/(t1-t0)*P0 + (t-t0)/(t1-t0)*P1
  A2 = (t2-t)/(t2-t1)*P1 + (t-t1)/(t2-t1)*P2
  A3 = (t3-t)/(t3-t2)*P2 + (t-t2)/(t3-t2)*P3
  #print(A1)
  #print(A2)
  #print(A3)
  B1 = (t2-t)/(t2-t0)*A1 + (t-t0)/(t2-t0)*A2
  B2 = (t3-t)/(t3-t1)*A2 + (t-t1)/(t3-t1)*A3

  C  = (t2-t)/(t2-t1)*B1 + (t-t1)/(t2-t1)*B2
  return C

def CatmullRomChain(P):
  """
  Calculate Catmull Rom for a chain of points and return the combined curve.
  """
  sz = len(P)

  # The curve C will contain an array of (x,y) points.
  C = []
  for i in range(sz-3):
    c = CatmullRomSpline(P[i], P[i+1], P[i+2], P[i+3])
    C.extend(c)

  return C

##############################################################################
#Execute example below if function python catmullrom.py is called 
# as main in terminal, else ignore

if __name__ == '__main__':

      # Define a set of points for curve to go through
      Torque = [[0,776],[0,775],[595,659],[1150,1400],[1190,552],[1200,0],[1200,-1]]
      Current = [[0,951],[0,950],[595,855],[1150,650],[1190,152],[1200,61],[1200,60]]
      # Calculate the Catmull-Rom splines through the points
      c_torque = CatmullRomChain(Torque)
      c_current = CatmullRomChain(Current)

      # Convert the Catmull-Rom curve points into x and y arrays and plot
      # x,y = zip(*c)
      # plt.plot(x,y)
      # # Plot the control points
      # px, py = zip(*Points)
      # plt.plot(px,py,'or')
      # plt.show()

      xRPM, yTorque=zip(*c_torque)
      xRPM, yCurrent=zip(*c_current)

      pxRPM, pyTorque =zip(*Torque)
      pxRPM, pyCurrent =zip(*Current)

      fig,ax1 =plt.subplots()

      color='tab:blue'
      ax1.plot(xRPM,yTorque,'b-',label='Torque curve')
      ax1.plot(pxRPM,pyTorque,'bo',label='Torque Data')

      ax1.tick_params(axis='y',labelcolor=color)
      ax1.set_xlabel('RPM')
      ax1.set_ylabel('Torque',color=color)
      ax1.set_xlim(0,1400)
      ax1.set_ylim(0,1600)
      ax1.set_xticks(numpy.arange(0, 1400, 200))
      ax1.set_yticks(numpy.arange(0, 1600, 200))

      ax2=ax1.twinx()
      color='tab:red'
      ax2.set_ylabel('Amps',color=color)
      ax2.plot(pxRPM,pyCurrent,'ro',label='Current data')
      ax2.plot(xRPM,yCurrent,'r-',label='Current curve')
      ax2.tick_params(axis='y',labelcolor=color)
      ax2.set_ylim(0,1000)

      ax1.yaxis.grid(True) # horizontal lines
      ax1.xaxis.grid(True) # vertical lines
      #fig.legend()
      fig.tight_layout()
      #plt.rc('grid', linestyle="--", color='black')

      #plt.grid(True)
      plt.show()