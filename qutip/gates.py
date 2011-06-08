#This file is part of QuTIP.
#
#    QuTIP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#    QuTIP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with QuTIP.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2011, Paul D. Nation & Robert J. Johansson
#
###########################################################################
from qstate import qstate
from Qobj import *

def cnot():
	"""
	Returns quantum object representing the CNOT gate.
	@brief CNOT gate
	@return Qobj quantum object representation of CNOT gate
	"""
	uu=qstate('uu')
	ud=qstate('ud')
	du=qstate('du')
	dd=qstate('dd')
	Q=dd*dag(dd)+du*dag(du)+uu*dag(ud)+ud*dag(uu)
	return Qobj(Q)

#------------------   
def snot():
	u=qstate('u')
	d=qstate('d')
	Q=((u+d)*dag(d)+(d-u)*dag(u))/sqrt(2)
	return Qobj(Q)


#------------------
def fredkin():
	"""
	Returns quantum object representing the Fredkin gate.
	@brief Freidkin gate
	@return Qobj quantum object representation of Fredkin gate
	"""
	uuu = qstate('uuu')
	uud = qstate('uud') 
	udu = qstate('udu')
	udd = qstate('udd')
	duu = qstate('duu') 
	dud = qstate('dud')
	ddu = qstate('ddu')
	ddd = qstate('ddd')
	Q = ddd*dag(ddd) + ddu*dag(ddu) + dud*dag(dud) + duu*dag(duu) + udd*dag(udd) + uud*dag(udu) + udu*dag(uud) + uuu*dag(uuu)
	return Qobj(Q)


#------------------
def toffoli():
	"""
	Returns quantum object representing the Toffoli gate.
	@brief Toffoli gate
	@return Qobj quantum object representation of Toffoli gate
	"""
	uuu = qstate('uuu') 
	uud = qstate('uud') 
	udu = qstate('udu') 
	udd = qstate('udd')
	duu = qstate('duu') 
	dud = qstate('dud') 
	ddu = qstate('ddu') 
	ddd = qstate('ddd')
	Q = ddd*dag(ddd) + ddu*dag(ddu) + dud*dag(dud) + duu*dag(duu) + udd*dag(udd) + udu*dag(udu) + uuu*dag(uud) + uud*dag(uuu)
	return Qobj(Q)

	
	
	
	