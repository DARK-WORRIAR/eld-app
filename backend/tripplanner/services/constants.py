"""
Federal Motor Carrier Safety Administration (FMCSA) Hours-of-Service (HOS)
regulatory constants and default operational parameters under 49 CFR Part 395
for property-carrying commercial motor vehicles.
"""

# ==============================================================================
# FMCSA 49 CFR § 395.3 - Maximum Driving Time for Property-Carrying Vehicles
# ==============================================================================

# Maximum consecutive driving hours allowed before required 10 consecutive hours off-duty
# Ref: 49 CFR § 395.3(a)(3)(i)
HOS_MAX_DRIVING_HOURS: float = 11.0

# Maximum consecutive elapsed duty window hours after coming on duty
# Driving is prohibited after the 14th hour following 10 consecutive hours off-duty.
# Ref: 49 CFR § 395.3(a)(2)
HOS_DUTY_WINDOW_HOURS: float = 14.0

# Mandatory rest break threshold: driver must take a 30-minute break after 8 cumulative
# hours of driving without at least a 30-minute interruption.
# Ref: 49 CFR § 395.3(a)(3)(ii)
HOS_BREAK_THRESHOLD_HOURS: float = 8.0

# Duration of mandatory rest break (30 minutes)
HOS_BREAK_DURATION_HOURS: float = 0.5

# Consecutive off-duty hours required to reset the 11-hour driving and 14-hour window clocks
# Ref: 49 CFR § 395.3(a)(1)
HOS_DAILY_RESET_HOURS: float = 10.0

# 70-hour / 8-day cycle limit for carriers operating every day of the week
# Ref: 49 CFR § 395.3(b)(2)
HOS_CYCLE_LIMIT_HOURS: float = 70.0

# 34-hour restart period to reset cumulative 70-hour duty cycle
# Ref: 49 CFR § 395.3(d)
HOS_CYCLE_RESTART_HOURS: float = 34.0


# ==============================================================================
# Standard Operational Assumptions & Fleet Defaults
# ==============================================================================

# Recommended fueling interval for Class 8 commercial tractors (miles)
DEFAULT_FUEL_INTERVAL_MILES: float = 1000.0

# Standard allotment for fueling and vehicle walk-around inspection (hours)
DEFAULT_FUEL_STOP_HOURS: float = 0.5

# Standard shipper dock time allotted for cargo pickup and paperwork (hours)
DEFAULT_PICKUP_HOURS: float = 1.0

# Standard receiver dock time allotted for cargo unloading and sign-off (hours)
DEFAULT_DROPOFF_HOURS: float = 1.0

# Fallback average cruising speed in miles per hour if route duration is missing/zero
DEFAULT_AVERAGE_SPEED_MPH: float = 50.0


# ==============================================================================
# Standard Duty Status Categories (FMCSA Form MCS-59 / ELD Technical Standard)
# ==============================================================================

DUTY_STATUS_OFF_DUTY = "off_duty"
DUTY_STATUS_SLEEPER_BERTH = "sleeper"
DUTY_STATUS_DRIVING = "driving"
DUTY_STATUS_ON_DUTY_NOT_DRIVING = "on_duty"

DUTY_STATUS_LABELS = {
    DUTY_STATUS_OFF_DUTY: "1. Off Duty",
    DUTY_STATUS_SLEEPER_BERTH: "2. Sleeper Berth",
    DUTY_STATUS_DRIVING: "3. Driving",
    DUTY_STATUS_ON_DUTY_NOT_DRIVING: "4. On Duty (Not Driving)",
}

