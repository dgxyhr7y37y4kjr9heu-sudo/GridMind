import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pandapower as pp
import math
import io
import zipfile
from datetime import datetime
from fpdf import FPDF

st.set_page_config(
    page_title="GridMind AI Enterprise Plus",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top left, #18375a 0%, #07111f 42%, #03070d 100%);
    color: white;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07111f, #050b13);
    border-right: 1px solid #1f3b5b;
}

h1, h2, h3, h4, p, label, span {
    color: white !important;
}

.main-title {
    font-size: 46px;
    font-weight: 900;
    margin-bottom: 0px;
}

.subtitle {
    color: #9fb3c8 !important;
    font-size: 16px;
}

.card {
    background: linear-gradient(180deg, rgba(20, 43, 69, 0.97), rgba(10, 22, 38, 0.97));
    border: 1px solid #245078;
    border-radius: 18px;
    padding: 18px;
    min-height: 118px;
    box-shadow: 0 0 22px rgba(0, 150, 255, 0.08);
}

.card-label {
    color: #9fb3c8 !important;
    font-size: 13px;
    margin-bottom: 8px;
}

.card-value {
    font-size: 27px;
    font-weight: 900;
}

.card-note {
    color: #8fa6bd !important;
    font-size: 12px;
    margin-top: 8px;
}

.green { color: #35e06f !important; }
.yellow { color: #ffd23f !important; }
.red { color: #ff4d4d !important; }
.blue { color: #33aaff !important; }
.purple { color: #b478ff !important; }

.panel {
    background: rgba(11, 23, 40, 0.94);
    border: 1px solid #1f3b5b;
    border-radius: 20px;
    padding: 22px;
    box-shadow: 0 0 18px rgba(0, 140, 255, 0.07);
}

.network {
    background: rgba(8, 18, 32, 0.94);
    border: 1px solid #1f3b5b;
    border-radius: 20px;
    padding: 26px;
    text-align: center;
    line-height: 2;
}

.bus {
    display: inline-block;
    background: #10263d;
    border: 1px solid #35e06f;
    border-radius: 13px;
    padding: 12px 18px;
    margin: 9px;
    min-width: 120px;
}

.bus-warn {
    border-color: #ffd23f;
}

.bus-danger {
    border-color: #ff4d4d;
}

.device {
    display: inline-block;
    background: #0f1f33;
    border: 1px solid #355c7d;
    border-radius: 13px;
    padding: 12px 18px;
    margin: 9px;
    min-width: 125px;
}

.arrow {
    color: #35e06f;
    font-weight: 900;
    padding: 0 8px;
}

.badge {
    display: inline-block;
    padding: 7px 14px;
    border-radius: 999px;
    font-weight: 900;
    font-size: 13px;
}

.badge-green {
    background: rgba(53, 224, 111, 0.12);
    border: 1px solid #35e06f;
    color: #35e06f !important;
}

.badge-yellow {
    background: rgba(255, 210, 63, 0.12);
    border: 1px solid #ffd23f;
    color: #ffd23f !important;
}

.badge-red {
    background: rgba(255, 77, 77, 0.12);
    border: 1px solid #ff4d4d;
    color: #ff4d4d !important;
}

.step {
    background: rgba(16, 38, 61, 0.95);
    border: 1px solid #245078;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 10px;
}

@media (max-width: 900px) {
    .main-title {
        font-size: 30px;
    }
    .subtitle {
        font-size: 13px;
    }
    .card {
        min-height: 95px;
        padding: 14px;
    }
    .card-value {
        font-size: 21px;
    }
    .network {
        padding: 12px;
    }
    .bus, .device {
        min-width: 92px;
        font-size: 12px;
        padding: 9px 10px;
        margin: 5px;
    }
}
</style>
""", unsafe_allow_html=True)


SCENARIOS = [
    "Base Case",
    "High Load",
    "Solar Enabled",
    "Night Peak",
    "Hospital Priority",
    "Fault Case",
    "Eco Mode"
]


def scenario_settings(name):
    data = {
        "Base Case": {
            "scale": 1.00, "solar": 2.0, "battery": 0.5,
            "ev_scale": 1.0, "line_factor": 1.0,
            "grid_vm": 1.02, "max_i": 0.42
        },
        "High Load": {
            "scale": 1.30, "solar": 1.5, "battery": 0.4,
            "ev_scale": 1.5, "line_factor": 1.15,
            "grid_vm": 1.01, "max_i": 0.40
        },
        "Solar Enabled": {
            "scale": 1.00, "solar": 4.8, "battery": 0.8,
            "ev_scale": 1.0, "line_factor": 1.0,
            "grid_vm": 1.02, "max_i": 0.42
        },
        "Night Peak": {
            "scale": 1.22, "solar": 0.0, "battery": 1.8,
            "ev_scale": 1.8, "line_factor": 1.2,
            "grid_vm": 1.01, "max_i": 0.40
        },
        "Hospital Priority": {
            "scale": 1.10, "solar": 2.2, "battery": 1.7,
            "ev_scale": 0.8, "line_factor": 1.0,
            "grid_vm": 1.02, "max_i": 0.42
        },
        "Fault Case": {
            "scale": 1.35, "solar": 0.7, "battery": 0.0,
            "ev_scale": 1.5, "line_factor": 2.5,
            "grid_vm": 1.00, "max_i": 0.27
        },
        "Eco Mode": {
            "scale": 0.82, "solar": 3.2, "battery": 1.2,
            "ev_scale": 0.7, "line_factor": 0.9,
            "grid_vm": 1.02, "max_i": 0.42
        }
    }
    return data[name]


def build_network(scenario, custom_load=1.0, custom_solar=1.0, custom_battery=1.0):
    s = scenario_settings(scenario)

    net = pp.create_empty_network(sn_mva=50)

    grid_132 = pp.create_bus(net, vn_kv=132, name="132kV Grid")
    sub_33 = pp.create_bus(net, vn_kv=33, name="33kV Substation")
    res_a = pp.create_bus(net, vn_kv=33, name="Residential A")
    res_b = pp.create_bus(net, vn_kv=33, name="Residential B")
    school = pp.create_bus(net, vn_kv=33, name="School Campus")
    mall = pp.create_bus(net, vn_kv=33, name="Commercial Mall")
    industrial = pp.create_bus(net, vn_kv=33, name="Industrial Load")
    hospital = pp.create_bus(net, vn_kv=33, name="Hospital Critical")
    ev_station = pp.create_bus(net, vn_kv=33, name="EV Charging")
    solar_farm = pp.create_bus(net, vn_kv=33, name="Solar Farm")

    pp.create_ext_grid(net, bus=grid_132, vm_pu=s["grid_vm"], va_degree=0.0, name="Utility Grid")

    pp.create_transformer_from_parameters(
        net,
        hv_bus=grid_132,
        lv_bus=sub_33,
        sn_mva=50,
        vn_hv_kv=132,
        vn_lv_kv=33,
        vk_percent=10.0,
        vkr_percent=0.6,
        pfe_kw=25,
        i0_percent=0.1,
        shift_degree=0,
        name="132/33 kV Transformer"
    )

    scale = s["scale"] * custom_load

    load_data = [
        ("Residential A", res_a, 1.8, 0.55, "Normal"),
        ("Residential B", res_b, 1.4, 0.42, "Normal"),
        ("School Campus", school, 0.9, 0.28, "Medium"),
        ("Commercial Mall", mall, 2.4, 0.85, "Medium"),
        ("Industrial Load", industrial, 4.7, 1.85, "High"),
        ("Hospital Critical", hospital, 2.0, 0.70, "Critical"),
        ("EV Charging", ev_station, 1.0 * s["ev_scale"], 0.30 * s["ev_scale"], "Flexible")
    ]

    for name, bus, p, q, priority in load_data:
        pp.create_load(net, bus=bus, p_mw=p * scale, q_mvar=q * scale, name=name)
        net.load.loc[net.load.index[-1], "priority"] = priority

    solar_power = s["solar"] * custom_solar
    battery_power = s["battery"] * custom_battery

    if solar_power > 0:
        pp.create_sgen(net, solar_farm, p_mw=solar_power, q_mvar=0.0, name="Solar Farm PV")

    if battery_power > 0:
        pp.create_sgen(net, hospital, p_mw=battery_power, q_mvar=0.0, name="Battery Storage")

    lf = s["line_factor"]
    max_i = s["max_i"]

    def line(a, b, length, r, x, name):
        pp.create_line_from_parameters(
            net,
            from_bus=a,
            to_bus=b,
            length_km=length * lf,
            r_ohm_per_km=r,
            x_ohm_per_km=x,
            c_nf_per_km=9,
            max_i_ka=max_i,
            name=name
        )

    line(sub_33, res_a, 3.5, 0.30, 0.17, "Substation to Residential A")
    line(res_a, res_b, 2.0, 0.32, 0.18, "Residential A to Residential B")
    line(sub_33, school, 2.5, 0.31, 0.17, "Substation to School")
    line(sub_33, mall, 3.0, 0.29, 0.16, "Substation to Commercial Mall")
    line(mall, ev_station, 2.2, 0.33, 0.18, "Mall to EV Station")
    line(sub_33, industrial, 4.2, 0.28, 0.16, "Substation to Industrial")
    line(sub_33, hospital, 3.0, 0.25, 0.15, "Substation to Hospital")
    line(sub_33, solar_farm, 3.8, 0.27, 0.15, "Substation to Solar Farm")
    line(hospital, mall, 2.7, 0.34, 0.19, "Backup Hospital to Mall")

    try:
        pp.runpp(net, calculate_voltage_angles=True, init="auto")
    except Exception:
        pp.runpp(net, calculate_voltage_angles=False, init="flat")

    return net


def analyze(net):
    total_load = float(net.res_load.p_mw.sum())

    solar = 0.0
    battery = 0.0

    if len(net.sgen) > 0:
        for idx, row in net.sgen.iterrows():
            p = float(net.res_sgen.loc[idx, "p_mw"])
            if row["name"] == "Solar Farm PV":
                solar += p
            elif row["name"] == "Battery Storage":
                battery += p

    grid_import = float(net.res_ext_grid.p_mw.sum())
    local_gen = solar + battery
    total_gen = max(grid_import, 0) + local_gen

    line_losses = float(net.res_line.pl_mw.sum())
    trafo_losses = float(net.res_trafo.pl_mw.sum()) if len(net.trafo) > 0 else 0.0
    losses = line_losses + trafo_losses

    min_voltage = float(net.res_bus.vm_pu.min())
    avg_voltage = float(net.res_bus.vm_pu.mean())
    max_line_loading = float(net.res_line.loading_percent.max())
    max_trafo_loading = float(net.res_trafo.loading_percent.max()) if len(net.trafo) > 0 else 0.0
    max_loading = max(max_line_loading, max_trafo_loading)

    loss_percent = (losses / total_load * 100) if total_load > 0 else 0

    weak_bus_index = int(net.res_bus.vm_pu.idxmin())
    weak_bus = str(net.bus.loc[weak_bus_index, "name"])

    health = 100
    health -= max(0, (0.95 - min_voltage) * 500)
    health -= max(0, (max_loading - 80) * 0.8)
    health -= min(loss_percent * 2.5, 25)
    health = max(0, min(100, health))

    if min_voltage < 0.90 or max_loading > 100:
        status = "Critical"
    elif min_voltage < 0.95 or max_loading > 80 or loss_percent > 5:
        status = "Warning"
    else:
        status = "Healthy"

    return {
        "total_load": total_load,
        "grid_import": grid_import,
        "solar": solar,
        "battery": battery,
        "local_gen": local_gen,
        "total_gen": total_gen,
        "losses": losses,
        "loss_percent": loss_percent,
        "min_voltage": min_voltage,
        "avg_voltage": avg_voltage,
        "weak_bus": weak_bus,
        "max_line_loading": max_line_loading,
        "max_trafo_loading": max_trafo_loading,
        "max_loading": max_loading,
        "health": health,
        "status": status
    }


def create_alarm_center(metrics, scenario):
    alarms = []

    if metrics["min_voltage"] < 0.90:
        alarms.append({
            "Severity": "Critical",
            "Alarm": "Severe Voltage Drop",
            "Location": metrics["weak_bus"],
            "Value": f"{metrics['min_voltage']:.3f} p.u.",
            "Recommendation": "Isolate weak feeder and support voltage using backup generation or capacitor bank."
        })
    elif metrics["min_voltage"] < 0.95:
        alarms.append({
            "Severity": "Warning",
            "Alarm": "Low Voltage",
            "Location": metrics["weak_bus"],
            "Value": f"{metrics['min_voltage']:.3f} p.u.",
            "Recommendation": "Monitor weak bus and increase voltage support."
        })

    if metrics["max_loading"] > 100:
        alarms.append({
            "Severity": "Critical",
            "Alarm": "Overload Condition",
            "Location": "Line or Transformer",
            "Value": f"{metrics['max_loading']:.1f}%",
            "Recommendation": "Trip overloaded section or redistribute load."
        })
    elif metrics["max_loading"] > 80:
        alarms.append({
            "Severity": "Warning",
            "Alarm": "High Loading",
            "Location": "Line or Transformer",
            "Value": f"{metrics['max_loading']:.1f}%",
            "Recommendation": "Reduce loading or use alternate feeder path."
        })

    if metrics["loss_percent"] > 5:
        alarms.append({
            "Severity": "Warning",
            "Alarm": "High Losses",
            "Location": "Distribution Network",
            "Value": f"{metrics['loss_percent']:.2f}%",
            "Recommendation": "Improve feeder routing or increase conductor capacity."
        })

    if scenario == "Fault Case":
        alarms.append({
            "Severity": "Critical",
            "Alarm": "Fault Scenario Active",
            "Location": "Network",
            "Value": "Fault Mode",
            "Recommendation": "Run fault diagnosis and isolate affected feeder."
        })

    if len(alarms) == 0:
        alarms.append({
            "Severity": "Normal",
            "Alarm": "No Active Alarms",
            "Location": "System",
            "Value": "OK",
            "Recommendation": "Continue monitoring system condition."
        })

    return pd.DataFrame(alarms)


def reliability_table(net):
    rows = []

    for idx, row in net.load.iterrows():
        bus_name = net.bus.loc[row["bus"], "name"]
        voltage = float(net.res_bus.loc[row["bus"], "vm_pu"])
        priority = row.get("priority", "Normal")

        if voltage < 0.90:
            risk = "Critical"
        elif voltage < 0.95:
            risk = "Warning"
        else:
            risk = "Normal"

        rows.append({
            "Load": row["name"],
            "Bus": bus_name,
            "Priority": priority,
            "Voltage p.u.": round(voltage, 4),
            "Risk": risk,
            "Restoration Action": "Restore first" if priority == "Critical" else "Normal restoration"
        })

    return pd.DataFrame(rows)


def forecast_dataframe(scenario, solar_peak):
    base = [
        3.0, 2.7, 2.5, 2.4, 2.6, 3.0,
        4.0, 5.2, 6.4, 7.4, 8.0, 8.5,
        8.9, 8.7, 8.2, 7.8, 7.3, 7.1,
        6.8, 6.2, 5.4, 4.6, 3.9, 3.4
    ]

    factor = {
        "Base Case": 1.0,
        "High Load": 1.25,
        "Solar Enabled": 0.95,
        "Night Peak": 1.15,
        "Hospital Priority": 1.08,
        "Fault Case": 1.25,
        "Eco Mode": 0.82
    }[scenario]

    solar_shape = [
        0, 0, 0, 0, 0, 0.05,
        0.18, 0.35, 0.55, 0.72, 0.88, 1.00,
        0.95, 0.82, 0.65, 0.45, 0.20, 0.05,
        0, 0, 0, 0, 0, 0
    ]

    rows = []
    battery_energy = 4.0
    battery_power_limit = 1.4

    for hour, load in enumerate(base):
        forecast_load = round(load * factor + 0.25 * math.sin(hour / 3), 3)
        solar = round(solar_peak * solar_shape[hour], 3)

        if hour in [17, 18, 19, 20] and battery_energy > 0:
            battery = min(battery_power_limit, battery_energy, max(0, forecast_load - solar - 4.5))
            battery_energy -= battery
        else:
            battery = 0.0

        grid = max(0, forecast_load - solar - battery)

        if 17 <= hour <= 21:
            price = 0.14
        elif 8 <= hour <= 16:
            price = 0.09
        else:
            price = 0.07

        cost = grid * price
        co2 = grid * 0.52

        rows.append({
            "Hour": hour,
            "Forecast Load MW": round(forecast_load, 3),
            "Solar MW": round(solar, 3),
            "Battery MW": round(battery, 3),
            "Grid Import MW": round(grid, 3),
            "Energy Cost $": round(cost, 3),
            "CO2 ton": round(co2, 3)
        })

    return pd.DataFrame(rows)


def comparison_dataframe():
    rows = []
    for sc in SCENARIOS:
        n = build_network(sc)
        m = analyze(n)
        rows.append({
            "Scenario": sc,
            "Load MW": round(m["total_load"], 3),
            "Generation MW": round(m["total_gen"], 3),
            "Losses MW": round(m["losses"], 4),
            "Loss %": round(m["loss_percent"], 3),
            "Min Voltage": round(m["min_voltage"], 4),
            "Weak Bus": m["weak_bus"],
            "Max Loading %": round(m["max_loading"], 2),
            "Health": round(m["health"], 1),
            "Status": m["status"]
        })
    return pd.DataFrame(rows)


def html_card(label, value, note, color):
    st.markdown(f"""
    <div class="card">
        <div class="card-label">{label}</div>
        <div class="card-value {color}">{value}</div>
        <div class="card-note">{note}</div>
    </div>
    """, unsafe_allow_html=True)


def status_badge(status):
    if status == "Healthy":
        return '<span class="badge badge-green">Healthy</span>'
    if status == "Warning":
        return '<span class="badge badge-yellow">Warning</span>'
    return '<span class="badge badge-red">Critical</span>'


def bus_class(v):
    if v < 0.90:
        return "bus bus-danger"
    if v < 0.95:
        return "bus bus-warn"
    return "bus"


def voltage_chart(net):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(net.bus.name),
        y=list(net.res_bus.vm_pu),
        mode="lines+markers+text",
        text=[f"{v:.3f}" for v in net.res_bus.vm_pu],
        textposition="top center",
        line=dict(width=4),
        marker=dict(size=10),
        name="Voltage"
    ))
    fig.add_hrect(y0=0.95, y1=1.05, fillcolor="green", opacity=0.08, line_width=0)
    fig.add_hline(y=0.95, line_dash="dash", line_color="orange")
    fig.add_hline(y=0.90, line_dash="dash", line_color="red")
    fig.update_layout(
        title="Voltage Profile",
        height=390,
        paper_bgcolor="#0b1728",
        plot_bgcolor="#0b1728",
        font_color="white",
        yaxis_title="Voltage p.u.",
        xaxis_title="Bus",
        yaxis=dict(range=[0.86, 1.07])
    )
    return fig


def loading_chart(net):
    names = list(net.line.name) + list(net.trafo.name)
    values = list(net.res_line.loading_percent) + list(net.res_trafo.loading_percent)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names,
        y=values,
        text=[f"{v:.1f}%" for v in values],
        textposition="auto",
        name="Loading"
    ))
    fig.add_hline(y=80, line_dash="dash", line_color="orange")
    fig.add_hline(y=100, line_dash="dash", line_color="red")
    fig.update_layout(
        title="Line and Transformer Loading",
        height=390,
        paper_bgcolor="#0b1728",
        plot_bgcolor="#0b1728",
        font_color="white",
        yaxis_title="Loading %",
        xaxis_title="Element"
    )
    return fig


def power_balance_chart(m):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Grid Import", "Solar", "Battery", "Losses"],
        y=[m["grid_import"], m["solar"], m["battery"], m["losses"]],
        text=[
            f"{m['grid_import']:.2f}",
            f"{m['solar']:.2f}",
            f"{m['battery']:.2f}",
            f"{m['losses']:.3f}"
        ],
        textposition="auto"
    ))
    fig.update_layout(
        title="Power Balance",
        height=390,
        paper_bgcolor="#0b1728",
        plot_bgcolor="#0b1728",
        font_color="white",
        yaxis_title="MW"
    )
    return fig


def forecast_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Hour"], y=df["Forecast Load MW"], mode="lines+markers", name="Forecast Load"))
    fig.add_trace(go.Scatter(x=df["Hour"], y=df["Solar MW"], mode="lines", name="Solar"))
    fig.add_trace(go.Scatter(x=df["Hour"], y=df["Battery MW"], mode="lines", name="Battery"))
    fig.add_trace(go.Scatter(x=df["Hour"], y=df["Grid Import MW"], mode="lines", name="Grid Import"))
    fig.update_layout(
        title="AI Load Forecast and Energy Management",
        height=430,
        paper_bgcolor="#0b1728",
        plot_bgcolor="#0b1728",
        font_color="white",
        xaxis_title="Hour",
        yaxis_title="MW"
    )
    return fig


def comparison_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["Scenario"], y=df["Losses MW"], name="Losses MW"))
    fig.add_trace(go.Scatter(x=df["Scenario"], y=df["Health"], mode="lines+markers", name="Health Score", yaxis="y2"))
    fig.update_layout(
        title="Scenario Comparison: Losses and Health",
        height=410,
        paper_bgcolor="#0b1728",
        plot_bgcolor="#0b1728",
        font_color="white",
        yaxis=dict(title="Losses MW"),
        yaxis2=dict(title="Health Score", overlaying="y", side="right", range=[0, 100])
    )
    return fig


def make_zip(summary, bus_df, line_df, trafo_df, comp_df, forecast_df, reliability_df, alarm_df):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("01_summary.csv", summary.to_csv(index=False))
        z.writestr("02_bus_results.csv", bus_df.to_csv(index=False))
        z.writestr("03_line_results.csv", line_df.to_csv(index=False))
        z.writestr("04_transformer_results.csv", trafo_df.to_csv(index=False))
        z.writestr("05_scenario_comparison.csv", comp_df.to_csv(index=False))
        z.writestr("06_forecast_energy_management.csv", forecast_df.to_csv(index=False))
        z.writestr("07_reliability_priority_loads.csv", reliability_df.to_csv(index=False))
        z.writestr("08_alarm_center.csv", alarm_df.to_csv(index=False))
    buffer.seek(0)
    return buffer


def make_pdf_report(summary_df, alarm_df, metrics):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    student_name = "Mohammed Ghazwan Nadhem Al-Shammari"
    university = "University of Basrah"
    department = "Department of Electrical Engineering"
    project_type = "Individual Project"

    def safe_text(value):
        text = str(value)
        text = text.replace("→", "to")
        text = text.replace("•", "-")
        text = text.replace("–", "-")
        text = text.replace("—", "-")
        return text.encode("latin-1", "ignore").decode("latin-1")

    def title(text):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Arial", "B", 17)
        pdf.multi_cell(pdf.epw, 8, safe_text(text))
        pdf.ln(2)

    def subtitle(text):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Arial", "B", 13)
        pdf.multi_cell(pdf.epw, 7, safe_text(text))
        pdf.ln(1)

    def paragraph(text):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(pdf.epw, 6, safe_text(text))
        pdf.ln(1)

    def key_value(key, value):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(55, 6, safe_text(str(key)), border=0)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(pdf.epw - 55, 6, safe_text(str(value)))

    # Cover / Header
    title("GridMind AI Enterprise Plus Report")
    paragraph("Smart Grid Digital Twin and Fault Intelligence Platform")

    subtitle("Project Information")
    key_value("University:", university)
    key_value("Department:", department)
    key_value("Project Type:", project_type)
    key_value("Student:", student_name)
    key_value("Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    pdf.ln(3)

    subtitle("Executive Summary")
    paragraph(
        "GridMind AI Enterprise Plus is a software-based smart grid digital twin. "
        "It simulates a distribution network, runs power flow analysis, evaluates voltage profile, "
        "line loading, transformer loading, losses, alarms, reliability, fault conditions, "
        "renewable energy support, battery operation, and engineering recommendations."
    )

    subtitle("System Components")
    paragraph(
        "- 132/33 kV transformer model\n"
        "- 33 kV distribution network\n"
        "- Residential, school, commercial, industrial, hospital, and EV loads\n"
        "- Solar farm and battery storage\n"
        "- Power flow engine using pandapower\n"
        "- Alarm Center and fault intelligence\n"
        "- Reliability and priority-load analysis\n"
        "- Exportable engineering reports"
    )

    pdf.add_page()

    title("Simulation Results")

    subtitle("Main Results")
    for _, row in summary_df.iterrows():
        key_value(row["Item"], row["Value"])

    pdf.ln(3)

    subtitle("Alarm Center")
    for _, row in alarm_df.iterrows():
        paragraph(
            f"Severity: {row['Severity']}\n"
            f"Alarm: {row['Alarm']}\n"
            f"Location: {row['Location']}\n"
            f"Value: {row['Value']}\n"
            f"Recommendation: {row['Recommendation']}"
        )

    subtitle("Engineering Recommendations")
    if metrics["status"] == "Critical":
        paragraph(
            "The network is operating in a critical condition. Immediate action is required. "
            "The recommended procedure is to isolate the weak or overloaded feeder, support voltage, "
            "and restore priority loads first."
        )
    elif metrics["status"] == "Warning":
        paragraph(
            "The network is close to an operating limit. The recommended action is to monitor the weak bus, "
            "use battery support during peak demand, and reduce loading on stressed feeders."
        )
    else:
        paragraph(
            "The network is operating normally. The recommended action is to continue monitoring, "
            "use solar generation during daytime, and keep checking voltage and loading limits."
        )

    subtitle("Engineering Interpretation")
    paragraph(
        "The results show how the electrical network behaves under the selected operating scenario. "
        "The minimum voltage indicates the weakest bus, the loading percentage indicates the stress on lines "
        "and transformer, while the power losses reflect network efficiency. The health score summarizes "
        "the overall operating condition of the grid."
    )

    subtitle("Conclusion")
    paragraph(
        "This project demonstrates how software tools can support smart grid analysis, renewable energy integration, "
        "fault diagnosis, alarm monitoring, and decision-making for electrical distribution systems."
    )

    output = pdf.output(dest="S")
    if isinstance(output, str):
        return output.encode("latin-1")
    return bytes(output)


st.sidebar.markdown("## ⚡ GridMind AI Enterprise Plus")
st.sidebar.caption("Smart Grid Operation Platform")

demo_mode = st.sidebar.checkbox("Demo Mode", value=False)

if demo_mode:
    demo_index = datetime.now().second // 8
    scenario = SCENARIOS[demo_index % len(SCENARIOS)]
    st.sidebar.info(f"Demo Mode Active: {scenario}")
else:
    scenario = st.sidebar.selectbox("Operating Scenario", SCENARIOS)

advanced = st.sidebar.checkbox("Advanced Controls", value=False)

if advanced:
    custom_load = st.sidebar.slider("Load Multiplier", 0.70, 1.70, 1.00, 0.05)
    custom_solar = st.sidebar.slider("Solar Multiplier", 0.00, 2.00, 1.00, 0.05)
    custom_battery = st.sidebar.slider("Battery Multiplier", 0.00, 2.00, 1.00, 0.05)
else:
    custom_load = 1.00
    custom_solar = 1.00
    custom_battery = 1.00

run_power_flow = st.sidebar.button("Run Real Power Flow")

net = build_network(scenario, custom_load, custom_solar, custom_battery)
m = analyze(net)
settings = scenario_settings(scenario)

st.sidebar.divider()
st.sidebar.markdown("### System Health")

if m["status"] == "Healthy":
    st.sidebar.success("Healthy")
elif m["status"] == "Warning":
    st.sidebar.warning("Warning")
else:
    st.sidebar.error("Critical")

st.sidebar.progress(int(m["health"]))
st.sidebar.caption(f"Health Score: {m['health']:.1f}/100")


bus_df = net.res_bus.copy()
bus_df.insert(0, "Bus", list(net.bus.name))

line_df = net.res_line.copy()
line_df.insert(0, "Line", list(net.line.name))

trafo_df = net.res_trafo.copy()
trafo_df.insert(0, "Transformer", list(net.trafo.name))

forecast_df = forecast_dataframe(scenario, settings["solar"] * custom_solar)
comparison_df = comparison_dataframe()
reliability_df = reliability_table(net)
alarm_df = create_alarm_center(m, scenario)

summary_df = pd.DataFrame({
    "Item": [
        "Date",
        "Scenario",
        "Total Load MW",
        "Grid Import MW",
        "Solar MW",
        "Battery MW",
        "Total Generation MW",
        "Power Losses MW",
        "Loss Percent",
        "Average Voltage",
        "Minimum Voltage",
        "Weakest Bus",
        "Max Loading",
        "Health Score",
        "Status"
    ],
    "Value": [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        scenario,
        f"{m['total_load']:.4f}",
        f"{m['grid_import']:.4f}",
        f"{m['solar']:.4f}",
        f"{m['battery']:.4f}",
        f"{m['total_gen']:.4f}",
        f"{m['losses']:.5f}",
        f"{m['loss_percent']:.4f}",
        f"{m['avg_voltage']:.5f}",
        f"{m['min_voltage']:.5f}",
        m["weak_bus"],
        f"{m['max_loading']:.3f}",
        f"{m['health']:.2f}",
        m["status"]
    ]
})


if "history" not in st.session_state:
    st.session_state.history = []

if run_power_flow:
    st.session_state.history.append({
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Scenario": scenario,
        "Load MW": round(m["total_load"], 3),
        "Losses MW": round(m["losses"], 4),
        "Min Voltage": round(m["min_voltage"], 4),
        "Weak Bus": m["weak_bus"],
        "Health": round(m["health"], 1),
        "Status": m["status"]
    })
    st.toast("Real Power Flow Completed Successfully ⚡")


head1, head2 = st.columns([4, 1])

with head1:
    st.markdown('<div class="main-title">⚡ GridMind AI Enterprise Plus</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Digital Twin • Power Flow • AI Forecasting • Fault Intelligence • Alarm Center • Reports</div>',
        unsafe_allow_html=True
    )

with head2:
    st.markdown(status_badge(m["status"]), unsafe_allow_html=True)
    st.caption("Enterprise Plus v3.0")


c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    html_card("Total Load", f"{m['total_load']:.2f} MW", "All active loads", "blue")
with c2:
    html_card("Generation", f"{m['total_gen']:.2f} MW", "Grid + solar + battery", "green")
with c3:
    html_card("Losses", f"{m['losses']:.3f} MW", f"{m['loss_percent']:.2f}% of load", "yellow")
with c4:
    color = "red" if m["min_voltage"] < 0.90 else "yellow" if m["min_voltage"] < 0.95 else "green"
    html_card("Min Voltage", f"{m['min_voltage']:.3f} p.u.", m["weak_bus"], color)
with c5:
    color = "red" if m["max_loading"] > 100 else "yellow" if m["max_loading"] > 80 else "green"
    html_card("Max Loading", f"{m['max_loading']:.1f}%", "Line/transformer limit", color)
with c6:
    color = "red" if m["health"] < 60 else "yellow" if m["health"] < 80 else "green"
    html_card("Health Score", f"{m['health']:.1f}", "Network condition", color)


tabs = st.tabs([
    "Home",
    "Dashboard",
    "Power Flow Lab",
    "Scenario Study",
    "AI Energy Management",
    "Fault Intelligence",
    "Alarm Center",
    "Reliability",
    "Historical Logs",
    "Reports",
    "Team",
    "Presentation"
])

tab_home, tab_dash, tab_lab, tab_study, tab_energy, tab_fault, tab_alarm, tab_reliability, tab_logs, tab_reports, tab_team, tab_present = tabs


with tab_home:
    st.markdown("### Project Overview")

    h1, h2, h3 = st.columns(3)

    with h1:
        st.markdown("""
        <div class="panel">
        <h3>Problem</h3>
        Traditional distribution networks can suffer from voltage drops, overloads, high losses,
        and poor renewable energy coordination.
        </div>
        """, unsafe_allow_html=True)

    with h2:
        st.markdown("""
        <div class="panel">
        <h3>Solution</h3>
        GridMind AI Enterprise Plus creates a digital twin of the grid and analyzes its operating
        condition using real power flow simulation.
        </div>
        """, unsafe_allow_html=True)

    with h3:
        st.markdown("""
        <div class="panel">
        <h3>Outputs</h3>
        Voltage profile, line loading, transformer loading, losses, health score,
        alarms, fault diagnosis, energy forecast, and engineering reports.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### System Architecture")

    a1, a2, a3, a4, a5 = st.columns(5)

    with a1:
        st.markdown('<div class="step">1. Input Scenario</div>', unsafe_allow_html=True)
    with a2:
        st.markdown('<div class="step">2. Build Digital Twin</div>', unsafe_allow_html=True)
    with a3:
        st.markdown('<div class="step">3. Run Power Flow</div>', unsafe_allow_html=True)
    with a4:
        st.markdown('<div class="step">4. AI Analysis</div>', unsafe_allow_html=True)
    with a5:
        st.markdown('<div class="step">5. Reports</div>', unsafe_allow_html=True)

    st.info("The project combines electrical engineering, smart grid operation, renewable energy, fault diagnosis, alarm monitoring, and reporting in one platform.")


with tab_dash:
    left, right = st.columns([2.4, 1])

    with left:
        st.markdown("### Digital Twin Network")

        v = dict(zip(net.bus.name, net.res_bus.vm_pu))

        st.markdown(f"""
        <div class="network">
            <span class="device">🌐 132kV Grid<br>{v['132kV Grid']:.3f} p.u.</span>
            <span class="arrow">━━</span>
            <span class="device">🔁 Transformer<br>132/33 kV</span>
            <span class="arrow">━━</span>
            <span class="{bus_class(v['33kV Substation'])}">33kV Substation<br>{v['33kV Substation']:.3f}</span>
            <br><br>
            <span class="{bus_class(v['Residential A'])}">Residential A<br>{v['Residential A']:.3f}</span>
            <span class="{bus_class(v['Residential B'])}">Residential B<br>{v['Residential B']:.3f}</span>
            <span class="{bus_class(v['School Campus'])}">School<br>{v['School Campus']:.3f}</span>
            <span class="{bus_class(v['Commercial Mall'])}">Mall<br>{v['Commercial Mall']:.3f}</span>
            <span class="{bus_class(v['Industrial Load'])}">Industrial<br>{v['Industrial Load']:.3f}</span>
            <span class="{bus_class(v['Hospital Critical'])}">Hospital<br>{v['Hospital Critical']:.3f}</span>
            <span class="{bus_class(v['EV Charging'])}">EV Station<br>{v['EV Charging']:.3f}</span>
            <span class="{bus_class(v['Solar Farm'])}">Solar Farm<br>{v['Solar Farm']:.3f}</span>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("### Smart Recommendations")
        if m["status"] == "Critical":
            st.error("Critical condition detected.")
            st.warning("Isolate overloaded or weak feeder.")
            st.info("Transfer priority loads to backup path.")
        elif m["status"] == "Warning":
            st.warning("Network is near a limit.")
            st.info("Use battery support at peak hours.")
            st.info(f"Monitor weak bus: {m['weak_bus']}")
        else:
            st.success("Network is operating normally.")
            st.info("Use solar generation during daytime.")
            st.info("Keep monitoring line loading.")

    x1, x2, x3 = st.columns(3)

    with x1:
        st.plotly_chart(voltage_chart(net), use_container_width=True)
    with x2:
        st.plotly_chart(loading_chart(net), use_container_width=True)
    with x3:
        st.plotly_chart(power_balance_chart(m), use_container_width=True)


with tab_lab:
    st.markdown("### Power Flow Laboratory")

    t1, t2, t3, t4, t5 = st.tabs(["Bus Results", "Line Results", "Transformer Results", "Load Data", "Generator Data"])

    with t1:
        st.dataframe(bus_df, use_container_width=True)
    with t2:
        st.dataframe(line_df, use_container_width=True)
    with t3:
        st.dataframe(trafo_df, use_container_width=True)
    with t4:
        st.dataframe(net.load, use_container_width=True)
    with t5:
        if len(net.sgen):
            st.dataframe(net.sgen, use_container_width=True)
        else:
            st.info("No local generators in this scenario.")


with tab_study:
    st.markdown("### Scenario Engineering Study")
    st.dataframe(comparison_df, use_container_width=True)
    st.plotly_chart(comparison_chart(comparison_df), use_container_width=True)

    best = comparison_df.sort_values("Health", ascending=False).iloc[0]
    worst = comparison_df.sort_values("Health", ascending=True).iloc[0]

    s1, s2 = st.columns(2)
    with s1:
        st.success(f"Best scenario: {best['Scenario']} with health score {best['Health']}")
    with s2:
        st.error(f"Weakest scenario: {worst['Scenario']} with health score {worst['Health']}")


with tab_energy:
    st.markdown("### AI Energy Management")

    l, r = st.columns([2, 1])

    with l:
        st.plotly_chart(forecast_chart(forecast_df), use_container_width=True)

    with r:
        peak_row = forecast_df.loc[forecast_df["Forecast Load MW"].idxmax()]
        total_cost = forecast_df["Energy Cost $"].sum()
        total_co2 = forecast_df["CO2 ton"].sum()
        solar_energy = forecast_df["Solar MW"].sum()
        battery_energy = forecast_df["Battery MW"].sum()

        html_card("Peak Forecast", f"{peak_row['Forecast Load MW']:.2f} MW", f"Hour {int(peak_row['Hour'])}:00", "yellow")
        st.write("")
        html_card("Daily Cost", f"${total_cost:.2f}", "Estimated imported energy cost", "blue")
        st.write("")
        html_card("CO2 Estimate", f"{total_co2:.2f} ton", "Grid import emissions", "purple")

    st.markdown("### Optimization Summary")
    st.info(f"Solar expected energy contribution: {solar_energy:.2f} MWh")
    st.info(f"Battery scheduled discharge: {battery_energy:.2f} MWh")
    st.warning("Recommended action: discharge battery during 17:00–20:00 peak window.")
    st.dataframe(forecast_df, use_container_width=True)


with tab_fault:
    st.markdown("### Fault Intelligence System")

    f1, f2 = st.columns([1, 2])

    with f1:
        fault_type = st.selectbox("Fault Type", ["Line-to-Ground", "Line-to-Line", "Three Phase Fault"])
        fault_location = st.selectbox(
            "Fault Location",
            ["Residential A", "Residential B", "School Campus", "Commercial Mall", "Industrial Load", "Hospital Critical", "EV Charging", "Solar Farm"]
        )
        severity = st.slider("Fault Severity", 10, 100, 70)
        run_fault = st.button("Analyze Fault")

    with f2:
        if run_fault:
            if fault_type == "Three Phase Fault":
                factor = 0.22
            elif fault_type == "Line-to-Line":
                factor = 0.38
            else:
                factor = 0.52

            voltage_map = dict(zip(net.bus.name, net.res_bus.vm_pu))
            base_voltage = voltage_map.get(fault_location, m["min_voltage"])

            estimated_voltage = max(0.05, base_voltage * factor * (100 / severity))
            estimated_fault_current = max(
                0.5,
                (m["total_load"] / (math.sqrt(3) * 33 * max(estimated_voltage, 0.1))) * 9
            )

            st.error("Fault Detected: System Unstable")
            st.write(f"**Fault Type:** {fault_type}")
            st.write(f"**Location:** {fault_location}")
            st.write(f"**Estimated Voltage During Fault:** {estimated_voltage:.3f} p.u.")
            st.write(f"**Estimated Fault Current:** {estimated_fault_current:.2f} kA")
            st.write("**Protection Decision:** Trip the affected feeder, isolate the faulted section, and restore healthy loads.")

            if fault_location == "Hospital Critical":
                st.warning("Priority warning: Hospital is a critical load. Backup supply must be restored first.")
            else:
                st.info("Priority action: Restore hospital and essential feeders first if outage occurs.")
        else:
            st.success("No active fault.")
            st.info("Choose fault type/location and run analysis.")

    st.markdown("### Protection Logic")
    st.markdown("""
    <div class="panel">
    <b>Protection rules:</b><br><br>
    • Voltage below 0.90 p.u. → Critical voltage condition<br>
    • Loading above 100% → Trip/overload condition<br>
    • Loading above 80% → Warning condition<br>
    • High losses → Efficiency warning<br>
    • Hospital load is treated as priority load during restoration
    </div>
    """, unsafe_allow_html=True)


with tab_alarm:
    st.markdown("### Alarm Center")
    st.dataframe(alarm_df, use_container_width=True)

    critical_count = len(alarm_df[alarm_df["Severity"] == "Critical"])
    warning_count = len(alarm_df[alarm_df["Severity"] == "Warning"])
    normal_count = len(alarm_df[alarm_df["Severity"] == "Normal"])

    a1, a2, a3 = st.columns(3)
    with a1:
        html_card("Critical Alarms", str(critical_count), "Immediate action required", "red")
    with a2:
        html_card("Warnings", str(warning_count), "Monitor condition", "yellow")
    with a3:
        html_card("Normal Messages", str(normal_count), "System information", "green")

    st.info("Alarm Center converts engineering results into operational messages and recommendations.")


with tab_reliability:
    st.markdown("### Reliability and Priority Load Analysis")
    st.dataframe(reliability_df, use_container_width=True)

    critical_loads = reliability_df[reliability_df["Priority"] == "Critical"]
    warning_loads = reliability_df[reliability_df["Risk"] != "Normal"]

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("### Critical Loads")
        st.dataframe(critical_loads, use_container_width=True)
    with r2:
        st.markdown("### Loads at Risk")
        if len(warning_loads) == 0:
            st.success("No priority loads currently at risk.")
        else:
            st.dataframe(warning_loads, use_container_width=True)

    st.info("Restoration policy: Hospital → Industrial essential feeder → Residential → Commercial → EV charging.")


with tab_logs:
    st.markdown("### Historical Operation Logs")

    if len(st.session_state.history) == 0:
        st.info("Press 'Run Real Power Flow' from the sidebar to store operation snapshots.")
    else:
        log_df = pd.DataFrame(st.session_state.history)
        st.dataframe(log_df, use_container_width=True)

        fig_log = go.Figure()
        fig_log.add_trace(go.Scatter(x=log_df["Time"], y=log_df["Health"], mode="lines+markers", name="Health"))
        fig_log.update_layout(
            title="Health Score History",
            height=350,
            paper_bgcolor="#0b1728",
            plot_bgcolor="#0b1728",
            font_color="white",
            yaxis=dict(range=[0, 100])
        )
        st.plotly_chart(fig_log, use_container_width=True)


with tab_reports:
    st.markdown("### Export Engineering Reports")

    st.dataframe(summary_df, use_container_width=True)

    zip_file = make_zip(summary_df, bus_df, line_df, trafo_df, comparison_df, forecast_df, reliability_df, alarm_df)
    pdf_file = make_pdf_report(summary_df, alarm_df, m)

    executive_report = f"""
# GridMind AI Enterprise Plus Report

Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Selected Scenario
{scenario}

## Main Results
- Total Load: {m["total_load"]:.3f} MW
- Grid Import: {m["grid_import"]:.3f} MW
- Solar Generation: {m["solar"]:.3f} MW
- Battery Discharge: {m["battery"]:.3f} MW
- Total Generation: {m["total_gen"]:.3f} MW
- Power Losses: {m["losses"]:.5f} MW
- Minimum Voltage: {m["min_voltage"]:.5f} p.u.
- Weakest Bus: {m["weak_bus"]}
- Maximum Loading: {m["max_loading"]:.3f} %
- Health Score: {m["health"]:.2f}
- System Status: {m["status"]}

## Engineering Interpretation
GridMind AI Enterprise Plus simulates a distribution network with transformer, solar PV, battery storage,
residential, school, commercial, industrial, hospital, and EV charging loads. It runs real power flow
analysis and provides forecasting, energy management, alarm monitoring, fault intelligence, reliability analysis, and reports.
"""

    x1, x2, x3, x4 = st.columns(4)

    with x1:
        st.download_button(
            "Download Full Report ZIP",
            data=zip_file,
            file_name="gridmind_ai_enterprise_plus_report.zip",
            mime="application/zip"
        )

    with x2:
        st.download_button(
            "Download PDF Report",
            data=pdf_file,
            file_name="gridmind_report.pdf",
            mime="application/pdf"
        )

    with x3:
        st.download_button(
            "Download Executive Report",
            data=executive_report.encode("utf-8"),
            file_name="gridmind_executive_report.md",
            mime="text/markdown"
        )

    with x4:
        st.download_button(
            "Download Summary CSV",
            data=summary_df.to_csv(index=False).encode("utf-8"),
            file_name="gridmind_summary.csv",
            mime="text/csv"
        )


with tab_team:
    st.markdown("### Team Page")

    st.markdown("""
    <div class="panel">
    <h3>Project Team</h3>
    <p><b>Project Name:</b> GridMind AI Enterprise Plus</p>
    <p><b>University:</b> University of Basrah</p>
    <p><b>Department:</b> Department of Electrical Engineering</p>
    <p><b>Project Type:</b> Individual Project</p>
    <p><b>Student:</b> Mohammed Ghazwan Nadhem Al-Shammari</p>
    <p><b>Field:</b> Electrical Engineering / Smart Grid Systems</p>
    <p><b>Tools:</b> Python, Streamlit, Pandapower, Plotly, Pandas, FPDF</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Student Role")
    st.info(
        "The student designed and implemented the software platform, built the electrical network model, "
        "performed power flow simulation, added forecasting, fault analysis, alarm monitoring, reliability analysis, "
        "and report generation."
    )

    st.markdown("### Academic Description")
    st.success(
        "This project represents an individual software-based engineering simulation system for smart grid operation "
        "and electrical distribution network analysis."
    )


with tab_present:
    st.markdown("### Presentation Material")

    st.markdown("""
    <div class="panel">
    <h3>Project Title</h3>
    <p><b>GridMind AI Enterprise Plus: Smart Grid Digital Twin and Fault Intelligence Platform</b></p>

    <h3>Project Idea</h3>
    <p>
    The project is a software platform that simulates and analyzes an electrical distribution network.
    It uses real power flow calculations to evaluate voltage profile, transformer loading,
    line loading, losses, renewable energy contribution, battery support, alarms, and fault conditions.
    </p>

    <h3>Main Components</h3>
    • 132/33 kV transformer<br>
    • 33 kV distribution network<br>
    • Residential, school, commercial, industrial, hospital, and EV loads<br>
    • Solar farm and battery storage<br>
    • Power flow engine<br>
    • AI-style load forecasting<br>
    • Alarm Center<br>
    • Fault diagnosis and protection recommendation<br>
    • Reliability and priority-load analysis<br>
    • Exportable engineering reports<br><br>

    <h3>Why It Is Important</h3>
    <p>
    The system helps engineers and students study grid operation safely without using real equipment.
    It can detect weak buses, voltage drops, overloaded feeders, high losses, and risky fault scenarios.
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.success(
        "Presentation line: Our project is a smart grid digital twin that combines electrical engineering, "
        "power flow analysis, renewable energy, AI-style forecasting, alarm monitoring, fault intelligence, "
        "reliability analysis, and automated reporting inside one professional software platform."
    )

st.caption("GridMind AI Enterprise Plus is an educational simulation platform and is not intended for controlling real power systems.")