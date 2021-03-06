import numpy as np
from scipy import integrate
from scipy.special import ellipkinc, ellipeinc

# calculate ellipsoid shape factors with elliptical integrals
def ellipsoid_shape_func(a, b, c):
    phi = np.arccos(c/a)
    m = (a**2.-b**2.)/(a**2.-c**2.)
    la = a*b*c/((a**2.-b**2.)*np.sqrt(a**2.-c**2.))*(ellipkinc(phi,m)-ellipeinc(phi,m))
    lc = b/(b**2.-c**2.)*(b-a*c/np.sqrt(a**2.-c**2.)*ellipeinc(phi,m))
    lb = 1.-la-lc
    return la, lb, lc

# integrate ellipsoid shape factors numerically
def ellipsoid_shape_facs(a, b, c):
    f = lambda x,av,bv,cv,dv : 0.5*av*bv*cv/((x+dv**2.)*
                               np.sqrt((x+av**2.)*(x+bv**2.)*(x+cv**2.)))

    la, err = integrate.quad(f, 0., np.inf, args=(a,b,c,a))
    lb, err = integrate.quad(f, 0., np.inf, args=(a,b,c,b))
    lc, err = integrate.quad(f, 0., np.inf, args=(a,b,c,c))

    return la, lb, lc

# ellipsoid polarizabilities
def ellipsoid_polz(diel, a, b, c):
    la, lb, lc = ellipsoid_shape_func(a, b, c)
    alph_a = 4./3.*np.pi*a*b*c*(diel-1.)/(1.+la*(diel-1.))
    alph_b = 4./3.*np.pi*a*b*c*(diel-1.)/(1.+lb*(diel-1.))
    alph_c = 4./3.*np.pi*a*b*c*(diel-1.)/(1.+lc*(diel-1.))

    return alph_a, alph_b, alph_c

# oblate spheroid (a=b>c) polarizabilities
def oblate_polz(diel, a, c):
    f = np.sqrt((a/c)**2.-1.)
    lc = (1.+f**2.)/f**2.*(1.-np.arctan(f)/f)
    la = (1.-lc)/2.
    alph_a = 4./3.*np.pi*a**2.*c*(diel-1.)/(1.+la*(diel-1.))
    alph_c = 4./3.*np.pi*a**2.*c*(diel-1.)/(1.+lc*(diel-1.))

    return alph_a, alph_a, alph_c

# prolate spheroid (a>b=c) polarizabilities
def prolate_polz(diel, a, b):
    ec = np.sqrt(1.-(b/a)**2.)
    la = (1.-ec**2.)/ec**2.*(1./(2.*ec)*np.log((1.+ec)/(1.-ec))-1.)
    lb = (1.-la)/2.
    alph_a = 4./3.*np.pi*b**2.*a*(diel-1.)/(1.+la*(diel-1.))
    alph_b = 4./3.*np.pi*b**2.*a*(diel-1.)/(1.+lb*(diel-1.))

    return alph_a, alph_b, alph_b

# anisotropic oblate spheroid (a=b>c) polarizabilities
def ani_oblate_polz(diel_a, diel_c, a, c):
    f = np.sqrt((a/c)**2.-1.)
    lc = (1.+f**2.)/f**2.*(1.-np.arctan(f)/f)
    la = (1.-lc)/2.
    alph_a = 4./3.*np.pi*a**2.*c*(diel_a-1.)/(1.+la*(diel_a-1.))
    alph_c = 4./3.*np.pi*a**2.*c*(diel_c-1.)/(1.+lc*(diel_c-1.))

    return alph_a, alph_a, alph_c

# spheroid inclusions with beta orientation dist
def eps_spheroid_beta(eps_inc, vfrac, angmom, a, c):
    ma = angmom[0]
    mc = angmom[1]
    if a>c:
        f = np.sqrt((a/c)**2.-1.)
        lc = (1.+f**2.)/f**2.*(1.-np.arctan(f)/f)
    else:
        ec = np.sqrt(1.-(a/c)**2.)
        lc = (1.-ec**2.)/ec**2.*(1./(2.*ec)*np.log((1.+ec)/(1.-ec))-1.)

    la = (1.-lc)/2.
    lam_a = 1./(1.+la*(eps_inc-1.))
    lam_c = 1./(1.+lc*(eps_inc-1.))

    # calculate effective dielectric tensor
    eps_a = (1.-vfrac+vfrac*eps_inc*(lam_a+ma*(lam_a-lam_c)))/(1.-vfrac+vfrac*(lam_a+ma*(lam_a-lam_c)))
    eps_c = (1.-vfrac+vfrac*eps_inc*(lam_c+mc*(lam_a-lam_c)))/(1.-vfrac+vfrac*(lam_c+mc*(lam_a-lam_c)))
    return eps_a, eps_c

# point spin orientation
def point_spin(phi_p, theta_p, phi_s, alpha_a, alpha_b, alpha_c):
    # create point rotation matrix
    cpp = np.cos(phi_p)
    ctp = np.cos(theta_p)
    spp = np.sin(phi_p)
    stp = np.sin(theta_p)
    apoint = np.array([[cpp*ctp,spp*ctp,-stp],
                       [-spp,cpp,0.],
                       [cpp*stp,spp*stp,ctp]])

    # create spin rotation matrix
    cps = np.cos(phi_s)
    sps = np.sin(phi_s)
    aspin = np.array([[cps,-sps,0.],
                       [sps,cps,0.],
                       [0.,0.,1.]])

    # transform polarizability tensor
    alpha_tensor = np.array([[alpha_a,0.,0.],
                             [0.,alpha_b,0.],
                             [0.,0.,alpha_c]])
    arot = np.matmul(aspin, apoint)
    alpha_rot = np.matmul(arot.T, np.matmul(alpha_tensor, arot))
    return alpha_rot

# scattering matrix from incident and scattering direction
# th_i - incident elevation angle from x-y plane
# ph_i - incident azimuthal angle from x axis
# th_s - scattering elevation angle from x-y plane
# ph_s - scattering azimuthal angle from x axis
def scat_matrix(th_i, phi_i, th_s, phi_s, alpha_tensor, k):
    # calculate incident field directions
    sti = np.sin(th_i)
    cti = np.cos(th_i)
    spi = np.sin(phi_i)
    cpi = np.cos(phi_i)
    apol_i = np.array([[-spi, cpi, 0.],
                       [-cpi*sti, -spi*sti, cti]])

    # calculate scattered field directions
    sts = np.sin(th_s)
    cts = np.cos(th_s)
    sps = np.sin(phi_s)
    cps = np.cos(phi_s)
    apol_s = np.array([[-sps, cps, 0.],
                       [-cps*sts, -sps*sts, cts]])
    alpha_pol = np.matmul(apol_s, np.matmul(alpha_tensor, apol_i.T))

    smat = k**2./(4.*np.pi)*alpha_pol
    return smat
