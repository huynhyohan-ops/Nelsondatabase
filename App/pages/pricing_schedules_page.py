from datetime import date

import pandas as pd
import streamlit as st


def _mock_best_rate_data():
    """Demo dữ liệu so sánh giá & lịch tàu."""

    best_option = {
        "carrier": "ONE",
        "service": "Weekly",
        "rate": 1250,
        "transit": "18d",
        "valid_to": "2025-03-15",
        "schedule_status": "Confirmed week 12",
        "notes": "Tối ưu giá/lead time; thêm phụ phí LSS",
    }

    comparison_rows = [
        {
            "Carrier": "ONE",
            "Service": "Direct",
            "20GP": 1250,
            "40HC": 1850,
            "Validity": "15 Mar",
            "ETD": "Thu",
            "Reliability": "Cao",
        },
        {
            "Carrier": "MSC",
            "Service": "Feeder",
            "20GP": 1320,
            "40HC": 1910,
            "Validity": "13 Mar",
            "ETD": "Fri",
            "Reliability": "Trung bình",
        },
        {
            "Carrier": "CMA",
            "Service": "Direct",
            "20GP": 1290,
            "40HC": 1890,
            "Validity": "Pending update",
            "ETD": "-",
            "Reliability": "Thiếu lịch",
        },
    ]

    schedule_rows = [
        {
            "Carrier": "ONE",
            "Vessel": "Morning Glory",
            "Week": "W12",
            "Cut-off": "Mon 16:00",
            "ETD": "Thu 22:00",
            "ETA": "+18d",
            "Status": "Confirmed",
        },
        {
            "Carrier": "MSC",
            "Vessel": "Carolina",
            "Week": "W12",
            "Cut-off": "Tue 12:00",
            "ETD": "Fri 20:00",
            "ETA": "+20d",
            "Status": "Pending update",
        },
        {
            "Carrier": "CMA",
            "Vessel": "TBN",
            "Week": "Auto pick by cargo ready",
            "Cut-off": "-",
            "ETD": "-",
            "ETA": "-",
            "Status": "Thiếu lịch từ carrier",
        },
    ]

    return best_option, pd.DataFrame(comparison_rows), pd.DataFrame(schedule_rows)


def _render_best_price_card(option: dict):
    """Card tóm tắt lựa chọn giá tối ưu."""

    with st.container():
        st.markdown(
            """
            <div class='info-card'>
                <div class='info-card-title'>Gợi ý tốt nhất</div>
                <div class='info-card-value'>{carrier} · {service}</div>
                <div class='info-card-sub'>${rate} / 20GP · Transit {transit}</div>
                <div class='info-card-sub'>Hiệu lực đến {valid_to} · {schedule_status}</div>
                <div class='info-card-sub' style='color:#111827;font-weight:600;margin-top:6px;'>
                    {notes}
                </div>
            </div>
            """.format(**option),
            unsafe_allow_html=True,
        )


def _week_label_from_mode(cargo_ready: date | None, mode: str) -> str:
    """Trả về nhãn tuần được sử dụng để tự động kiểm tra lịch."""

    if mode == "Ngày cargo ready" and cargo_ready:
        week_no = cargo_ready.isocalendar().week
        return f"Tuần cargo ready (W{week_no:02d})"

    today = date.today()
    week_no = today.isocalendar().week
    return f"Tuần hiện tại (W{week_no:02d})"


def _data_quality_summary(df_schedule: pd.DataFrame) -> tuple[str, list[str]]:
    """Đếm nhanh các trạng thái lịch để nhấn mạnh phần thiếu dữ liệu."""

    missing_rows = df_schedule[df_schedule["Status"].str.contains("Thiếu", case=False, na=False)]
    pending_rows = df_schedule[df_schedule["Status"].str.contains("Pending", case=False, na=False)]

    summary = "Dữ liệu lịch đã sẵn sàng."
    bullet_points = []

    if len(missing_rows) or len(pending_rows):
        summary = "Một số hãng chưa cập nhật đủ lịch."

    if len(missing_rows):
        bullet_points.append(f"{len(missing_rows)} tuyến thiếu ETD/ETA rõ ràng (đánh dấu 'Thiếu lịch').")

    if len(pending_rows):
        bullet_points.append(f"{len(pending_rows)} tuyến đang chờ xác nhận ('Pending update').")

    if not bullet_points:
        bullet_points.append("Tất cả lịch đều đã có ETD/ETA và trạng thái xác nhận.")

    return summary, bullet_points


def render_schedules_page():
    """Lịch tàu & kiểm tra giá tối ưu theo tuần hoặc cargo ready."""

    st.markdown(
        "<div class='section-title'>Schedules – Lịch tàu / lịch giao nhận</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>Kiểm tra nhanh giá tốt nhất và lịch tàu hợp lệ theo tuần hiện tại hoặc ngày cargo ready. Tập trung vào thao tác nhanh và minh bạch dữ liệu.</div>",
        unsafe_allow_html=True,
    )

    with st.container():
        col_filters, col_actions = st.columns([2, 1])

        with col_filters:
            st.markdown("#### Bộ lọc hành trình")
            pol = st.text_input("POL", value="HCM")
            pod = st.text_input("POD / POD alt", value="Los Angeles")
            cargo_ready = st.date_input("Cargo ready / Actual date")
            service_type = st.selectbox("Loại dịch vụ", ["Any", "Direct", "Feeder"], index=1)
            container_type = st.multiselect(
                "Số lượng container",
                options=["1 x 20GP", "1 x 40HC", "2 x 40HC"],
                default=["1 x 20GP", "1 x 40HC"],
            )

        with col_actions:
            st.markdown("#### Tự động hoá kiểm tra")
            week_mode = st.radio(
                "Cập nhật lịch dựa trên",
                options=["Tuần hiện tại", "Ngày cargo ready"],
                index=0,
            )
            st.toggle("Ưu tiên giá thấp nhất", value=True)
            st.toggle("Đánh dấu carrier thiếu lịch", value=True)
            st.toggle("Hiển thị phụ phí & ghi chú", value=True)
            st.caption(
                "Ứng dụng sẽ tự động đối chiếu tuần hiện tại (hoặc ngày cargo ready) để gợi ý lịch phù hợp và đánh dấu các hãng chưa đủ dữ liệu."
            )

    st.markdown("---")

    best_option, df_comparison, df_schedule = _mock_best_rate_data()
    week_label = _week_label_from_mode(cargo_ready, week_mode)
    quality_summary, quality_bullets = _data_quality_summary(df_schedule)

    st.success(
        f"Kiểm tra tự động đang dùng {week_label}. Đầu vào POL={pol}, POD={pod}, dịch vụ={service_type}, containers={', '.join(container_type) if container_type else '-'}.",
        icon="✅",
    )

    st.markdown("### Kết quả gợi ý nhanh")
    _render_best_price_card(best_option)

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("#### So sánh giá & hiệu lực")
        st.dataframe(
            df_comparison,
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            (
                "Bảng giá được tự động lọc theo {mode} với POL={pol}, POD={pod}, "
                "dịch vụ={service}, container={containers}. Cargo ready: {cargo_ready}."
            ).format(
                mode=week_mode.lower(),
                pol=pol or "-",
                pod=pod or "-",
                service=service_type,
                containers=", ".join(container_type) if container_type else "-",
                cargo_ready=cargo_ready,
            )
        )

    with c2:
        st.markdown("#### Các nhắc nhở dữ liệu")
        st.info(quality_summary)
        for bullet in quality_bullets:
            st.write(f"- {bullet}")
        st.warning(
            "Nếu chọn 'Ngày cargo ready', hệ thống sẽ ưu tiên tuần phù hợp nhất và cảnh báo nếu tuần đó chưa có tàu."
        )

    st.markdown("### Lịch tàu theo tuần / ngày")
    st.dataframe(df_schedule, hide_index=True, use_container_width=True)
    st.caption(
        "Lịch được phân nhóm theo tuần hiện tại hoặc ngày cargo ready. Các dòng 'Thiếu lịch' cho biết dữ liệu schedule chưa đầy đủ từ carrier."
    )

    st.markdown("---")
    st.markdown("#### Điều hướng nhanh")
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    with quick_col1:
        st.button("🔁 Làm mới theo tuần hiện tại", use_container_width=True)
    with quick_col2:
        st.button("📥 Xuất bảng giá & lịch", use_container_width=True)
    with quick_col3:
        st.button("📞 Gửi yêu cầu confirm tàu", use_container_width=True)
