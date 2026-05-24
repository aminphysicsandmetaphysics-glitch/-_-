import { useState } from "react";
import { api } from "../api/client";

export function WeatherInput({ buildingId }: { buildingId: number }) {
  const [days, setDays] = useState(365);

  async function generateSample() {
    const start = new Date("2024-03-20");
    const rows = Array.from({ length: days }, (_, index) => {
      const date = new Date(start);
      date.setDate(start.getDate() + index);
      const seasonal = 17 + 13 * Math.sin((2 * Math.PI * (index - 80)) / 365);
      return {
        city: "جاجرم",
        date: date.toISOString().slice(0, 10),
        temp_min: seasonal - 7,
        temp_max: seasonal + 7,
        temp_avg: seasonal,
        humidity: 35 + 15 * Math.sin((2 * Math.PI * (index + 40)) / 365),
        solar_radiation: Math.max(1, 5.5 + 2.5 * Math.sin((2 * Math.PI * (index - 90)) / 365)),
        rainfall: index % 27 === 0 ? 4 : 0,
        wind_speed: 2.5,
      };
    });
    await api.saveWeather(buildingId, rows);
    alert("Sample Jajarm weather data saved. Excel upload endpoint is available in the API.");
  }

  return (
    <section className="panel">
      <p className="eyebrow">Step 3 | Weather Data Input</p>
      <h2>Jajarm Climate Data | داده‌های هواشناسی جاجرم</h2>
      <p>Required format: Date, Min Temp, Max Temp, Mean Temp, Humidity, Solar Radiation, Rainfall, Wind Speed.</p>
      <label className="year-field">
        Sample days
        <input type="number" value={days} onChange={(event) => setDays(Number(event.target.value))} />
      </label>
      <button className="primary" onClick={generateSample}>Generate sample weather year</button>
    </section>
  );
}
