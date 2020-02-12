import sys

sys.path.append('glac1d_meltwater')
import routing
import spreading
import plotting
import glac1d_toolbox as tb
import xarray as xr
import numpy as np
import numpy.ma as ma
import os
import datetime


# --------------------------------- #
# ---------- MAIN METHOD ---------- #
# --------------------------------- #

def saving(discharge_mw, ds_lsm, lsm_name, mode):
    print("__ Saving algorithm")

    lsm, longitude, latitude = ds_lsm.lsm.values, ds_lsm.longitude.values, ds_lsm.latitude.values

    if mode == "routed":
        routed_to_netcdf(discharge_mw, lsm, longitude, latitude, lsm_name)
    elif mode == "spreaded":
        spreaded_to_netcdf(discharge_mw, lsm, longitude, latitude, lsm_name)
    else:
        print("The mode wasn't recognized.")


def fixing(ds_ref, mode_fixing, mode_smooth, start, end, lsm_name):
    print("__ Fixing algorithm")

    ref_mw, longitude, latitude, t_ref = \
        ds_ref.discharge.values, ds_ref.longitude.values, ds_ref.latitude.values, ds_ref.t.values

    if mode_fixing == "time":
        processed_mw, processed_time = process_time(ref_mw, start, end, t_ref)
        processed_to_netcdf(processed_mw, processed_time, longitude, latitude, mode_smooth, start, end, lsm_name)
    else:
        print("The mode wasn't recognized.")


# ------------------------------------ #
# ---------- SAVING METHODS ---------- #
# ------------------------------------ #

def routed_to_netcdf(spreaded_mw, lsm, longitude, latitude, lsm_name):
    """
    Create default netcdf differential file with time from -26 to 0 and 100 time steps. To modify that use process_time.
    :param spreaded_mw:
    :param lsm:
    :param longitude:
    :param latitude:
    :return:
    """

    # m3/s to kg/m2/s
    processed_mask = m3s_to_kgm2s(spreaded_mw, longitude, latitude)

    masked_mw = masking_method(processed_mask, lsm)

    # time fix
    time = np.arange(-26000, 100, 100)

    #
    sav_path = f"/nfs/annie/eeymr/work/outputs/Proj_GLAC1D/dif_-26_0/{lsm_name}.qrparm.GLAC1D_DEGLAC.nc"
    print(f"____ Saving at: {sav_path}")

    # to netcdf
    ds = xr.Dataset({'discharge': (('t', 'latitude', 'longitude'), masked_mw)},
                    coords={'t': time, 'latitude': latitude,
                            'longitude': longitude})
    ds['discharge'].attrs['units'] = 'kg m-2 s-1'
    ds['discharge'].attrs['longname'] = 'P-E FLUX CORRECTION       KG/M2/S  A'
    # ds['discharge'].attrs['_FillValue'] = 9.96921e+36
    # ds['discharge'].attrs['missingvalue'] = 9.96921e+36

    ds['t'].attrs['long_name'] = 'time'
    ds['t'].attrs['units'] = 'years since 0000-01-01 00:00:00'
    ds['t'].attrs['calendar'] = '360_days'

    ds['longitude'].attrs['long_name'] = 'longitude'
    ds['longitude'].attrs['actual_range'] = '0., 359.'
    ds['longitude'].attrs['axis'] = 'X'
    ds['longitude'].attrs['units'] = 'degrees_east'
    ds['longitude'].attrs['modulo'] = '360'
    ds['longitude'].attrs['topology'] = 'circular'

    ds['latitude'].attrs['long_name'] = 'latitude'
    ds['latitude'].attrs['actual_range'] = '-89.5, 89.5'
    ds['latitude'].attrs['axis'] = 'y'
    ds['latitude'].attrs['units'] = 'degrees_north'

    ds.attrs['title'] = \
        f"waterfix for transient GLAC1D last delgaciation HadCM3 project - {lsm_name} land sea mask"
    ds.attrs['history'] = f"Created {datetime.datetime.now()} by Yvan Romé"

    ds.to_netcdf(sav_path)


def spreaded_to_netcdf(spreaded_mw, lsm, longitude, latitude, lsm_name):
    """
    Create default netcdf file with time from -26 to 0 and 100 time steps. To modify that use process_time.
    :param spreaded_mw:
    :param lsm:
    :param longitude:
    :param latitude:
    :return:
    """

    # m3/s to kg/m2/s
    processed_mask = m3s_to_kgm2s(spreaded_mw, longitude, latitude)

    masked_mw = masking_method(processed_mask, lsm)

    # time fix
    time = np.arange(-26000, 100, 100)

    #
    sav_path = f"/nfs/annie/eeymr/work/outputs/Proj_GLAC1D/dif_-26_0_s/{lsm_name}.qrparm.waterfix_GLAC1D_DEGLAC_s.nc"
    print(f"____ Saving at: {sav_path}")

    # to netcdf
    ds = xr.Dataset({'discharge': (('t', 'latitude', 'longitude'), masked_mw)},
                    coords={'t': time, 'latitude': latitude,
                            'longitude': longitude})
    ds['discharge'].attrs['units'] = 'kg m-2 s-1'
    ds['discharge'].attrs['longname'] = 'P-E FLUX CORRECTION       KG/M2/S  A'
    # ds['discharge'].attrs['_FillValue'] = 9.96921e+36
    # ds['discharge'].attrs['missingvalue'] = 9.96921e+36

    ds['t'].attrs['long_name'] = 'time'
    ds['t'].attrs['units'] = 'years since 0000-01-01 00:00:00'
    ds['t'].attrs['calendar'] = '360_days'

    ds['longitude'].attrs['long_name'] = 'longitude'
    ds['longitude'].attrs['actual_range'] = '0., 359.'
    ds['longitude'].attrs['axis'] = 'X'
    ds['longitude'].attrs['units'] = 'degrees_east'
    ds['longitude'].attrs['modulo'] = '360'
    ds['longitude'].attrs['topology'] = 'circular'

    ds['latitude'].attrs['long_name'] = 'latitude'
    ds['latitude'].attrs['actual_range'] = '-89.5, 89.5'
    ds['latitude'].attrs['axis'] = 'y'
    ds['latitude'].attrs['units'] = 'degrees_north'

    ds.attrs['title'] = \
        f"waterfix for transient GLAC1D last delgaciation HadCM3 project - {lsm_name} land sea mask"
    ds.attrs['history'] = f"Created {datetime.datetime.now()} by Yvan Romé"

    ds.to_netcdf(sav_path)


def processed_to_netcdf(processed_mw, processed_time, longitude, latitude, mode_smooth, start, end, lsm_name):
    """
    Create default netcdf file with time from -26 to 0 and 100 time steps. To modify that use process_time.
    :param ds_mw: in kg/m2/s
    :param lsm:
    :param longitude:
    :param latitude:
    :return:
    """

    #
    sav_path = f"/nfs/annie/eeymr/work/outputs/Proj_GLAC1D/{mode_smooth}_{start}_{end}_s/{lsm_name}.qrparm.waterfix_GLAC1D_DEGLAC_s.nc"
    print(f"____ Saving at: {sav_path}")

    # to netcdf
    ds = xr.Dataset({'discharge': (('t', 'latitude', 'longitude'), processed_mw)},
                    coords={'t': processed_time, 'latitude': latitude,
                            'longitude': longitude})
    ds['discharge'].attrs['units'] = 'kg m-2 s-1'
    ds['discharge'].attrs['longname'] = 'P-E FLUX CORRECTION       KG/M2/S  A'

    ds['t'].attrs['long_name'] = 'time'
    ds['t'].attrs['units'] = 'years since 0000-01-01 00:00:00'
    ds['t'].attrs['calendar'] = '360_days'

    ds['longitude'].attrs['long_name'] = 'longitude'
    ds['longitude'].attrs['actual_range'] = '0., 359.'
    ds['longitude'].attrs['axis'] = 'X'
    ds['longitude'].attrs['units'] = 'degrees_east'
    ds['longitude'].attrs['modulo'] = '360'
    ds['longitude'].attrs['topology'] = 'circular'

    ds['latitude'].attrs['long_name'] = 'latitude'
    ds['latitude'].attrs['actual_range'] = '-89.5, 89.5'
    ds['latitude'].attrs['axis'] = 'y'
    ds['latitude'].attrs['units'] = 'degrees_north'

    ds.attrs['title'] = \
        f"waterfix for transient GLAC1D last delgaciation HadCM3 project - {lsm_name} land sea mask"
    ds.attrs['history'] = f"Created {datetime.datetime.now()} by Yvan Romé"

    ds.to_netcdf(sav_path)


def create_output_folder(mode, start, end, spreaded):
    # Create directory

    if mode == "differential":
        mode_name = "dif"
    else:
        mode_name = "nodif"

    spreaded_name = (spreaded is True) * "_s"

    dir_name = f"/nfs/annie/eeymr/work/outputs/Proj_GLAC1D/{mode_name}_{start}_{end}{spreaded_name}"

    try:
        # Create target Directory
        os.mkdir(dir_name)
        print("Directory ", dir_name, " Created ")
    except FileExistsError:
        print("Directory ", dir_name, " already exists")


# ---------------------------------------- #
# ---------- CONVERSION METHODS ---------- #
# ---------------------------------------- #

def masking_method(mw, lsm):
    lsm_3d = np.resize(lsm, mw.shape)
    return ma.array(mw, mask=lsm_3d)


def m3s_to_kgm2s(mw, lon, lat):
    d = 1000  # water density
    return np.divide(mw * 1000, tb.surface_matrix(lon, lat))


# ---------------------------------------- #
# ---------- PROCESSING METHODS ---------- #
# ---------------------------------------- #

def process_time(ref_mw, start, end, t_ref):
    """
    When the we want an extend different from the reference data set, it is faster and more convenient to process directly the previous outputs.
    :param ref_mw:
    :param start:
    :param end:
    :return:
    """
    start_k, end_k = start*1000, end*1000
    processed_time = np.arange(start_k, end_k + 100, 100)
    n_t, n_lat, n_lon = ref_mw.shape
    processed_mw = np.zeros((len(processed_time), n_lat, n_lon))

    if (start >= -26) and (end <= 0):
        id_start = np.where(t_ref == start_k)[0][0]
        id_end = np.where(t_ref == end_k)[0][0]

        processed_mw[:] = ref_mw[id_start:id_end + 1]

    elif (start < -26) and (end <= 0):
        id_26 = np.where(processed_time == -26000)[0][0]
        id_end = np.where(t_ref == end_k)[0][0]

        processed_mw[:id_26] = ref_mw[0]
        processed_mw[id_26:] = ref_mw[:id_end]

    elif (start >= -26) and (end > 0):
        id_start = np.where(t_ref == start_k)[0][0]
        id_0 = np.where(processed_time == 0)[0][0]

        processed_mw[:id_0] = ref_mw[id_start:]
        processed_mw[id_0:] = ref_mw[-1]

    elif (start < -26) and (end > 0):
        id_26 = np.where(processed_time == -26000)[0][0]
        id_0 = np.where(processed_time == 0)[0][0]

        processed_mw[:id_26] = ref_mw[0]
        processed_mw[id_26: id_0+1] = ref_mw[:]
        processed_mw[id_0:] = ref_mw[-1]

    else:
        raise ValueError("!!! Start or end paramters incorect")

    return processed_mw, processed_time