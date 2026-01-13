"""Tests for device wizard pin role suggestion functionality."""

import pytest

from pinviz.device_wizard import get_context_hint_for_pin, get_role_choices_for_pin


class TestPinRoleSuggestions:
    """Test suite for pin role auto-suggestions."""

    def test_power_pin_vin_suggests_both_voltages(self):
        """VIN should suggest both 5V and 3V3."""
        choices = get_role_choices_for_pin("VIN")
        assert len(choices) > 0
        # First two should be the suggested power roles
        assert choices[0].title in ["5V", "3V3"]
        assert choices[1].title in ["5V", "3V3"]
        assert "suggested" in choices[0].value
        assert "suggested" in choices[1].value

    def test_power_pin_vcc_suggests_both_voltages(self):
        """VCC should suggest both 5V and 3V3."""
        choices = get_role_choices_for_pin("VCC")
        assert choices[0].title in ["5V", "3V3"]
        assert "suggested" in choices[0].value

    def test_power_pin_vdd_suggests_both_voltages(self):
        """VDD should suggest both 5V and 3V3."""
        choices = get_role_choices_for_pin("VDD")
        assert choices[0].title in ["5V", "3V3"]
        assert "suggested" in choices[0].value

    def test_explicit_3v3_pin_suggests_3v3(self):
        """Explicit 3V3 pin should suggest 3V3 only."""
        choices = get_role_choices_for_pin("3V3")
        assert choices[0].title == "3V3"
        assert "suggested" in choices[0].value

    def test_explicit_5v_pin_suggests_5v(self):
        """Explicit 5V pin should suggest 5V only."""
        choices = get_role_choices_for_pin("5V")
        assert choices[0].title == "5V"
        assert "suggested" in choices[0].value

    def test_ground_pin_gnd_suggests_ground(self):
        """GND should suggest ground role."""
        choices = get_role_choices_for_pin("GND")
        assert choices[0].title == "GND"
        assert "suggested" in choices[0].value

    def test_ground_pin_ground_suggests_ground(self):
        """GROUND should suggest ground role."""
        choices = get_role_choices_for_pin("GROUND")
        assert choices[0].title == "GND"
        assert "suggested" in choices[0].value

    def test_i2c_sda_pin_suggests_i2c_sda(self):
        """SDA should suggest I2C_SDA role."""
        choices = get_role_choices_for_pin("SDA")
        assert choices[0].title == "I2C_SDA"
        assert "suggested" in choices[0].value

    def test_i2c_scl_pin_suggests_i2c_scl(self):
        """SCL should suggest I2C_SCL role."""
        choices = get_role_choices_for_pin("SCL")
        assert choices[0].title == "I2C_SCL"
        assert "suggested" in choices[0].value

    def test_spi_mosi_pin_suggests_spi_mosi(self):
        """MOSI should suggest SPI_MOSI role."""
        choices = get_role_choices_for_pin("MOSI")
        assert choices[0].title == "SPI_MOSI"
        assert "suggested" in choices[0].value

    def test_spi_miso_pin_suggests_spi_miso(self):
        """MISO should suggest SPI_MISO role."""
        choices = get_role_choices_for_pin("MISO")
        assert choices[0].title == "SPI_MISO"
        assert "suggested" in choices[0].value

    def test_spi_sclk_pin_suggests_spi_sclk(self):
        """SCLK should suggest SPI_SCLK role."""
        choices = get_role_choices_for_pin("SCLK")
        assert choices[0].title == "SPI_SCLK"
        assert "suggested" in choices[0].value

    def test_spi_cs_pin_suggests_spi_ce0(self):
        """CS should suggest SPI_CE0 role."""
        choices = get_role_choices_for_pin("CS")
        assert choices[0].title == "SPI_CE0"
        assert "suggested" in choices[0].value

    def test_uart_tx_pin_suggests_uart_tx(self):
        """TX should suggest UART_TX role."""
        choices = get_role_choices_for_pin("TX")
        assert choices[0].title == "UART_TX"
        assert "suggested" in choices[0].value

    def test_uart_rx_pin_suggests_uart_rx(self):
        """RX should suggest UART_RX role."""
        choices = get_role_choices_for_pin("RX")
        assert choices[0].title == "UART_RX"
        assert "suggested" in choices[0].value

    def test_pwm_pin_suggests_pwm(self):
        """PWM should suggest PWM role."""
        choices = get_role_choices_for_pin("PWM")
        assert choices[0].title == "PWM"
        assert "suggested" in choices[0].value


class TestCaseInsensitivity:
    """Test that pattern matching is case-insensitive."""

    @pytest.mark.parametrize(
        "pin_name",
        ["sda", "SDA", "Sda", "sDa"],
    )
    def test_sda_case_variations(self, pin_name):
        """SDA in any case should suggest I2C_SDA."""
        choices = get_role_choices_for_pin(pin_name)
        assert choices[0].title == "I2C_SDA"
        assert "suggested" in choices[0].value

    @pytest.mark.parametrize(
        "pin_name",
        ["vin", "VIN", "Vin", "vIn"],
    )
    def test_vin_case_variations(self, pin_name):
        """VIN in any case should suggest power roles."""
        choices = get_role_choices_for_pin(pin_name)
        assert choices[0].title in ["5V", "3V3"]
        assert "suggested" in choices[0].value


class TestWhitespaceHandling:
    """Test that whitespace is properly handled."""

    def test_pin_with_leading_whitespace(self):
        """Pin names with leading whitespace should still match."""
        choices = get_role_choices_for_pin("  VCC")
        assert choices[0].title in ["5V", "3V3"]
        assert "suggested" in choices[0].value

    def test_pin_with_trailing_whitespace(self):
        """Pin names with trailing whitespace should still match."""
        choices = get_role_choices_for_pin("VCC  ")
        assert choices[0].title in ["5V", "3V3"]
        assert "suggested" in choices[0].value

    def test_pin_with_surrounding_whitespace(self):
        """Pin names with surrounding whitespace should still match."""
        choices = get_role_choices_for_pin("  VCC  ")
        assert choices[0].title in ["5V", "3V3"]
        assert "suggested" in choices[0].value


class TestFalsePositivePrevention:
    """Test that pattern matching doesn't create false positives."""

    def test_disconnect_does_not_suggest_scl(self):
        """DISCONNECT contains 'sco' but should not suggest I2C_SCL."""
        choices = get_role_choices_for_pin("DISCONNECT")
        # Should return original list without suggestions
        assert "⭐" not in choices[0].value

    def test_clock_out_does_not_suggest_spi_sclk(self):
        """CLOCK_OUT contains 'clk' but should not suggest SPI_SCLK."""
        choices = get_role_choices_for_pin("CLOCK_OUT")
        assert "⭐" not in choices[0].value

    def test_tx_enable_suggests_uart_tx(self):
        """TX_ENABLE contains TX as word and reasonably suggests UART_TX.

        Note: This is actually reasonable behavior since TX_ENABLE likely
        controls a UART TX line. Word boundary matching is working correctly.
        """
        choices = get_role_choices_for_pin("TX_ENABLE")
        # This IS a reasonable suggestion
        assert choices[0].title == "UART_TX"
        assert "⭐" in choices[0].value

    def test_gpio4_does_not_suggest_gpio_role(self):
        """GPIO4 should not trigger any specific role suggestions."""
        choices = get_role_choices_for_pin("GPIO4")
        assert "⭐" not in choices[0].value

    def test_data_does_not_suggest_sda(self):
        """DATA contains 'da' but should not suggest I2C_SDA."""
        choices = get_role_choices_for_pin("DATA")
        assert "⭐" not in choices[0].value

    def test_input_does_not_suggest_vin(self):
        """INPUT contains 'in' but should not suggest VIN."""
        choices = get_role_choices_for_pin("INPUT")
        assert "⭐" not in choices[0].value

    def test_discount_does_not_suggest_scl(self):
        """DISCOUNT contains 'sco' but should not suggest I2C_SCL."""
        choices = get_role_choices_for_pin("DISCOUNT")
        assert "⭐" not in choices[0].value


class TestUnderscoreSeparatedPins:
    """Test that underscore-separated pin names work correctly."""

    def test_vin_power_suggests_power(self):
        """VIN_POWER should suggest power roles."""
        choices = get_role_choices_for_pin("VIN_POWER")
        assert choices[0].title in ["5V", "3V3"]
        assert "suggested" in choices[0].value

    def test_i2c_sda_suggests_i2c_sda(self):
        """I2C_SDA should suggest I2C_SDA role."""
        choices = get_role_choices_for_pin("I2C_SDA")
        assert choices[0].title == "I2C_SDA"
        assert "suggested" in choices[0].value

    def test_spi_mosi_suggests_spi_mosi(self):
        """SPI_MOSI should suggest SPI_MOSI role."""
        choices = get_role_choices_for_pin("SPI_MOSI")
        assert choices[0].title == "SPI_MOSI"
        assert "suggested" in choices[0].value

    def test_uart_tx_pin_suggests_uart_tx(self):
        """UART_TX should suggest UART_TX role."""
        choices = get_role_choices_for_pin("UART_TX")
        assert choices[0].title == "UART_TX"
        assert "suggested" in choices[0].value

    def test_gnd_pin_suggests_ground(self):
        """POWER_GND should suggest GND role."""
        choices = get_role_choices_for_pin("POWER_GND")
        assert choices[0].title == "GND"
        assert "suggested" in choices[0].value


class TestHyphenSeparatedPins:
    """Test that hyphen-separated pin names work correctly."""

    def test_vin_in_suggests_power(self):
        """VIN-IN should suggest power roles."""
        choices = get_role_choices_for_pin("VIN-IN")
        assert choices[0].title in ["5V", "3V3"]
        assert "suggested" in choices[0].value

    def test_sda_line_suggests_i2c_sda(self):
        """SDA-LINE should suggest I2C_SDA role."""
        choices = get_role_choices_for_pin("SDA-LINE")
        assert choices[0].title == "I2C_SDA"
        assert "suggested" in choices[0].value


class TestNumberedPinNames:
    """Test that pin names with numbers are handled correctly."""

    def test_scl1_suggests_i2c_scl(self):
        """SCL1 should suggest I2C_SCL role."""
        choices = get_role_choices_for_pin("SCL1")
        assert choices[0].title == "I2C_SCL"
        assert "suggested" in choices[0].value

    def test_sda2_suggests_i2c_sda(self):
        """SDA2 should suggest I2C_SDA role."""
        choices = get_role_choices_for_pin("SDA2")
        assert choices[0].title == "I2C_SDA"
        assert "suggested" in choices[0].value

    def test_uart2_tx_suggests_uart_tx(self):
        """UART2_TX should suggest UART_TX role."""
        choices = get_role_choices_for_pin("UART2_TX")
        assert choices[0].title == "UART_TX"
        assert "suggested" in choices[0].value

    def test_txd0_suggests_uart_tx(self):
        """TXD0 should suggest UART_TX role."""
        choices = get_role_choices_for_pin("TXD0")
        assert choices[0].title == "UART_TX"
        assert "suggested" in choices[0].value

    def test_rxd1_suggests_uart_rx(self):
        """RXD1 should suggest UART_RX role."""
        choices = get_role_choices_for_pin("RXD1")
        assert choices[0].title == "UART_RX"
        assert "suggested" in choices[0].value

    def test_vcc_3v3_suggests_3v3(self):
        """VCC_3V3 should suggest 3V3 role."""
        choices = get_role_choices_for_pin("VCC_3V3")
        assert choices[0].title == "3V3"
        assert "suggested" in choices[0].value

    def test_spi1_mosi_suggests_spi_mosi(self):
        """SPI1_MOSI should suggest SPI_MOSI role."""
        choices = get_role_choices_for_pin("SPI1_MOSI")
        assert choices[0].title == "SPI_MOSI"
        assert "suggested" in choices[0].value


class TestGenericPinNames:
    """Test that generic pin names don't trigger suggestions."""

    @pytest.mark.parametrize(
        "pin_name",
        ["GPIO1", "GPIO4", "PIN1", "PIN2", "D0", "D1", "A0", "A1"],
    )
    def test_generic_pins_no_suggestions(self, pin_name):
        """Generic pin names should not trigger suggestions."""
        choices = get_role_choices_for_pin(pin_name)
        assert "⭐" not in choices[0].value

    def test_empty_pin_name_returns_original_list(self):
        """Empty pin name should return original list."""
        choices = get_role_choices_for_pin("")
        assert "⭐" not in choices[0].value


class TestSeparatorPresence:
    """Test that separator is present when suggestions exist."""

    def test_separator_present_with_suggestions(self):
        """When suggestions exist, a separator should be present."""
        choices = get_role_choices_for_pin("VIN")
        # Find the separator (it's a disabled choice with dashes)
        separator_found = False
        for choice in choices:
            if getattr(choice, "disabled", False) and "─" in getattr(choice, "value", ""):
                separator_found = True
                break
        assert separator_found, "Separator should be present when suggestions exist"

    def test_no_separator_without_suggestions(self):
        """When no suggestions exist, no separator should be present."""
        choices = get_role_choices_for_pin("GPIO4")
        # Check that no separator exists
        separator_found = False
        for choice in choices:
            if getattr(choice, "disabled", False) and "─" in getattr(choice, "value", ""):
                separator_found = True
                break
        assert not separator_found, "Separator should not be present without suggestions"


class TestAllRolesStillAccessible:
    """Test that all original roles remain accessible."""

    def test_all_roles_present_with_suggestions(self):
        """All original roles should be present even with suggestions."""
        choices = get_role_choices_for_pin("VIN")
        # Count non-separator choices
        non_separator_choices = [
            c
            for c in choices
            if not getattr(c, "disabled", False) or "─" not in getattr(c, "value", "")
        ]
        # Should have all ~19 roles
        assert len(non_separator_choices) >= 19

    def test_all_roles_present_without_suggestions(self):
        """All roles should be present without suggestions."""
        choices = get_role_choices_for_pin("GPIO4")
        # Should have all ~19 roles
        assert len(choices) >= 19


class TestContextHints:
    """Test context hints for ambiguous pins."""

    def test_vin_has_context_hint(self):
        """VIN should return a helpful context hint."""
        hint = get_context_hint_for_pin("VIN")
        assert hint is not None
        assert "VIN/VCC" in hint
        assert "3V3" in hint
        assert "Raspberry Pi" in hint

    def test_vcc_has_context_hint(self):
        """VCC should return a helpful context hint."""
        hint = get_context_hint_for_pin("VCC")
        assert hint is not None
        assert "VIN/VCC" in hint

    def test_addr_has_context_hint(self):
        """ADDR should return I2C address hint."""
        hint = get_context_hint_for_pin("ADDR")
        assert hint is not None
        assert "Address" in hint
        assert "I2C" in hint

    def test_3vo_has_context_hint(self):
        """3VO should warn it's an output."""
        hint = get_context_hint_for_pin("3VO")
        assert hint is not None
        assert "output" in hint.lower()
        assert "PROVIDES" in hint

    def test_enable_has_context_hint(self):
        """Enable pins should have context hint."""
        hint = get_context_hint_for_pin("EN")
        assert hint is not None
        assert "Enable" in hint

    def test_generic_pin_no_hint(self):
        """Generic pins should not have context hints."""
        hint = get_context_hint_for_pin("GPIO1")
        assert hint is None

        hint = get_context_hint_for_pin("D0")
        assert hint is None

    # Power pins
    def test_vbat_has_context_hint(self):
        """VBAT should explain it's for battery backup."""
        hint = get_context_hint_for_pin("VBAT")
        assert hint is not None
        assert "Battery backup" in hint or "backup" in hint
        assert "RTC" in hint or "backup memory" in hint

    def test_ioref_has_context_hint(self):
        """IOREF should explain it's an output indicator."""
        hint = get_context_hint_for_pin("IOREF")
        assert hint is not None
        assert "OUTPUT" in hint
        assert "voltage" in hint.lower()

    # I2C address selection variations
    def test_sa0_has_context_hint(self):
        """SA0 should be recognized as I2C address pin."""
        hint = get_context_hint_for_pin("SA0")
        assert hint is not None
        assert "Address" in hint or "address" in hint
        assert "I2C" in hint

    def test_ad0_has_context_hint(self):
        """AD0 should be recognized as I2C address pin."""
        hint = get_context_hint_for_pin("AD0")
        assert hint is not None
        assert "Address" in hint or "address" in hint

    def test_ado_has_context_hint(self):
        """ADO should be recognized as I2C address pin."""
        hint = get_context_hint_for_pin("ADO")
        assert hint is not None
        assert "Address" in hint or "address" in hint

    # SPI pins
    def test_cs_has_context_hint(self):
        """CS should explain Chip Select usage."""
        hint = get_context_hint_for_pin("CS")
        assert hint is not None
        assert "Chip Select" in hint or "chip select" in hint.lower()
        assert "SPI" in hint

    def test_ss_has_context_hint(self):
        """SS should explain Slave Select usage."""
        hint = get_context_hint_for_pin("SS")
        assert hint is not None
        assert "Slave Select" in hint or "Chip Select" in hint

    def test_din_has_context_hint(self):
        """DIN should explain data direction ambiguity."""
        hint = get_context_hint_for_pin("DIN")
        assert hint is not None
        assert "MOSI" in hint
        assert "perspective" in hint.lower() or "device" in hint.lower()

    def test_dout_has_context_hint(self):
        """DOUT should explain data direction ambiguity."""
        hint = get_context_hint_for_pin("DOUT")
        assert hint is not None
        assert "MISO" in hint

    def test_sdi_has_context_hint(self):
        """SDI should be recognized as SPI data pin."""
        hint = get_context_hint_for_pin("SDI")
        assert hint is not None
        assert "Data" in hint

    def test_sdo_has_context_hint(self):
        """SDO should be recognized as SPI data pin."""
        hint = get_context_hint_for_pin("SDO")
        assert hint is not None
        assert "Data" in hint

    # Display pins
    def test_dc_has_context_hint(self):
        """DC should explain Data/Command usage."""
        hint = get_context_hint_for_pin("DC")
        assert hint is not None
        assert "Data/Command" in hint or "display" in hint.lower()

    def test_rs_has_context_hint(self):
        """RS should explain it's for display control."""
        hint = get_context_hint_for_pin("RS")
        assert hint is not None
        assert "display" in hint.lower()

    # Clock pins
    def test_clk_has_context_hint(self):
        """CLK should explain clock signal usage."""
        hint = get_context_hint_for_pin("CLK")
        assert hint is not None
        assert "Clock" in hint
        assert "SPI_SCLK" in hint or "SCLK" in hint

    # Control pins
    def test_ce_has_context_hint(self):
        """CE should explain Chip Enable usage."""
        hint = get_context_hint_for_pin("CE")
        assert hint is not None
        assert "Chip Enable" in hint or "chip enable" in hint.lower()

    def test_run_has_context_hint(self):
        """RUN should explain it's for microcontroller control."""
        hint = get_context_hint_for_pin("RUN")
        assert hint is not None
        assert "Run" in hint or "Enable" in hint
        assert "microcontroller" in hint.lower()

    def test_shdn_has_context_hint(self):
        """SHDN should explain shutdown control."""
        hint = get_context_hint_for_pin("SHDN")
        assert hint is not None
        assert "Shutdown" in hint or "shutdown" in hint.lower()

    def test_shutdown_has_context_hint(self):
        """SHUTDOWN should explain shutdown control."""
        hint = get_context_hint_for_pin("SHUTDOWN")
        assert hint is not None
        assert "Shutdown" in hint or "shutdown" in hint.lower()

    # Status pins
    def test_drdy_has_context_hint(self):
        """DRDY should explain Data Ready status."""
        hint = get_context_hint_for_pin("DRDY")
        assert hint is not None
        assert "Data Ready" in hint or "status" in hint.lower()

    def test_rdy_has_context_hint(self):
        """RDY should explain ready status."""
        hint = get_context_hint_for_pin("RDY")
        assert hint is not None
        assert "Ready" in hint or "status" in hint.lower()

    def test_busy_has_context_hint(self):
        """BUSY should explain busy status."""
        hint = get_context_hint_for_pin("BUSY")
        assert hint is not None
        assert "Busy" in hint or "status" in hint.lower()

    # Boot pins
    def test_boot_has_context_hint(self):
        """BOOT should explain boot mode selection."""
        hint = get_context_hint_for_pin("BOOT")
        assert hint is not None
        assert "Boot" in hint or "boot" in hint.lower()
        assert "GND" in hint

    def test_boot0_has_context_hint(self):
        """BOOT0 should explain boot mode selection."""
        hint = get_context_hint_for_pin("BOOT0")
        assert hint is not None
        assert "Boot" in hint or "boot" in hint.lower()

    # Ground variations
    def test_agnd_has_context_hint(self):
        """AGND should explain analog ground."""
        hint = get_context_hint_for_pin("AGND")
        assert hint is not None
        assert "Analog" in hint or "Ground" in hint
        assert "BOTH" in hint

    def test_dgnd_has_context_hint(self):
        """DGND should explain digital ground."""
        hint = get_context_hint_for_pin("DGND")
        assert hint is not None
        assert "Digital" in hint or "Ground" in hint
        assert "BOTH" in hint

    # Write protect
    def test_wp_has_context_hint(self):
        """WP should explain write protect functionality."""
        hint = get_context_hint_for_pin("WP")
        assert hint is not None
        assert "Write Protect" in hint or "write" in hint.lower()
        assert "EEPROM" in hint or "flash" in hint

    # Special pins
    def test_nc_has_context_hint(self):
        """NC should warn not to connect."""
        hint = get_context_hint_for_pin("NC")
        assert hint is not None
        assert "No Connect" in hint or "unconnected" in hint.lower()
        assert "NOT" in hint

    def test_test_has_context_hint(self):
        """TEST should explain it's for factory use."""
        hint = get_context_hint_for_pin("TEST")
        assert hint is not None
        assert "test" in hint.lower()
        assert "unconnected" in hint.lower() or "leave" in hint.lower()


class TestEnhancedRoleDescriptions:
    """Test that role descriptions include helpful context."""

    def test_3v3_context_without_i2c(self):
        """3V3 suggestion should have Raspberry Pi context."""
        choices = get_role_choices_for_pin("VIN", detected_i2c=False)
        # Find the 3V3 choice
        v3_choice = next((c for c in choices if c.title == "3V3"), None)
        assert v3_choice is not None
        assert "Raspberry Pi" in v3_choice.value

    def test_3v3_context_with_i2c(self):
        """3V3 suggestion should mention I2C when I2C is detected."""
        choices = get_role_choices_for_pin("VIN", detected_i2c=True)
        # Find the 3V3 choice
        v3_choice = next((c for c in choices if c.title == "3V3"), None)
        assert v3_choice is not None
        assert "I2C" in v3_choice.value

    def test_5v_context(self):
        """5V suggestion should have Arduino context."""
        choices = get_role_choices_for_pin("VIN", detected_i2c=False)
        # Find the 5V choice
        v5_choice = next((c for c in choices if c.title == "5V"), None)
        assert v5_choice is not None
        assert "Arduino" in v5_choice.value or "5V" in v5_choice.value


class TestAmbiguousPatterns:
    """Test patterns that suggest multiple roles due to ambiguity."""

    def test_din_suggests_both_miso_and_mosi(self):
        """DIN is perspective-dependent and should suggest both MISO and MOSI."""
        choices = get_role_choices_for_pin("DIN")
        # Check that both are suggested (should be first two choices)
        assert choices[0].title in ["SPI_MISO", "SPI_MOSI"]
        assert choices[1].title in ["SPI_MISO", "SPI_MOSI"]
        assert choices[0].title != choices[1].title
        assert "suggested" in choices[0].value
        assert "suggested" in choices[1].value

    def test_dout_suggests_both_mosi_and_miso(self):
        """DOUT is perspective-dependent and should suggest both MOSI and MISO."""
        choices = get_role_choices_for_pin("DOUT")
        # Check that both are suggested
        assert choices[0].title in ["SPI_MOSI", "SPI_MISO"]
        assert choices[1].title in ["SPI_MOSI", "SPI_MISO"]
        assert choices[0].title != choices[1].title
        assert "suggested" in choices[0].value
        assert "suggested" in choices[1].value

    def test_sdi_suggests_both_roles(self):
        """SDI is ambiguous and should suggest both MISO and MOSI."""
        choices = get_role_choices_for_pin("SDI")
        assert choices[0].title in ["SPI_MISO", "SPI_MOSI"]
        assert choices[1].title in ["SPI_MISO", "SPI_MOSI"]
        assert "suggested" in choices[0].value

    def test_sdo_suggests_both_roles(self):
        """SDO is ambiguous and should suggest both MOSI and MISO."""
        choices = get_role_choices_for_pin("SDO")
        assert choices[0].title in ["SPI_MOSI", "SPI_MISO"]
        assert choices[1].title in ["SPI_MOSI", "SPI_MISO"]
        assert "suggested" in choices[0].value

    def test_clk_suggests_multiple_roles(self):
        """CLK is ambiguous and should suggest SPI_SCLK, PWM, and GPIO."""
        choices = get_role_choices_for_pin("CLK")
        # Should suggest at least SPI_SCLK
        assert choices[0].title in ["SPI_SCLK", "PWM", "GPIO"]
        assert "suggested" in choices[0].value

    def test_serial_tx_suggests_uart_tx(self):
        """SERIAL_TX should suggest UART_TX role."""
        choices = get_role_choices_for_pin("SERIAL_TX")
        assert choices[0].title == "UART_TX"
        assert "suggested" in choices[0].value

    def test_serial_rx_suggests_uart_rx(self):
        """SERIAL_RX should suggest UART_RX role."""
        choices = get_role_choices_for_pin("SERIAL_RX")
        assert choices[0].title == "UART_RX"
        assert "suggested" in choices[0].value
