from colorsys import rgb_to_hls, hls_to_rgb

class ThemeColorConverter:
    RGBMAX = 0xff
    HLSMAX = 240

    def __init__(self, wb):
        self.colors = self.get_theme_colors(wb)

    @staticmethod
    def tint_luminance(tint, lum):
        if tint < 0:
            return int(round(lum * (1.0 + tint)))
        return int(round((ThemeColorConverter.HLSMAX - lum) * tint)) + lum

    @staticmethod
    def ms_hls_to_rgb(hue, lightness=None, saturation=None):
        if lightness is None:
            hue, lightness, saturation = hue
        hlsmax = ThemeColorConverter.HLSMAX
        return hls_to_rgb(hue / hlsmax, lightness / hlsmax, saturation / hlsmax)

    @staticmethod
    def rgb_to_hex(red, green=None, blue=None):
        if green is None:
            red, green, blue = red
        return '{:02X}{:02X}{:02X}'.format(
            int(red * ThemeColorConverter.RGBMAX),
            int(green * ThemeColorConverter.RGBMAX),
            int(blue * ThemeColorConverter.RGBMAX)
        )

    @staticmethod
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2,4))

    @staticmethod
    def rgb_to_ms_hls(red, green=None, blue=None):
        if green is None:
            if isinstance(red, str):
                if len(red) > 6:
                    red = red[-6:]  # Ignore preceding '#' and alpha values
                rgbmax = ThemeColorConverter.RGBMAX
                blue = int(red[4:], 16) / rgbmax
                green = int(red[2:4], 16) / rgbmax
                red = int(red[0:2], 16) / rgbmax
            else:
                red, green, blue = red
        h, l, s = rgb_to_hls(red, green, blue)
        hlsmax = ThemeColorConverter.HLSMAX
        return (int(round(h * hlsmax)), int(round(l * hlsmax)),
                int(round(s * hlsmax)))

    @staticmethod
    def get_theme_colors(wb):
        from openpyxl.xml.functions import QName, fromstring
        xlmns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        root = fromstring(wb.loaded_theme)
        themeEl = root.find(QName(xlmns, 'themeElements').text)
        colorSchemes = themeEl.findall(QName(xlmns, 'clrScheme').text)
        firstColorScheme = colorSchemes[0]
        colors = []
        for c in ['lt1', 'dk1', 'lt2', 'dk2', 'accent1', 'accent2', 'accent3', 'accent4', 'accent5', 'accent6']:
            accent = firstColorScheme.find(QName(xlmns, c).text)
            for i in list(accent):
                if 'window' in i.attrib['val']:
                    colors.append(i.attrib['lastClr'])
                else:
                    colors.append(i.attrib['val'])
        return colors

    def theme_and_tint_to_rgb(self, theme, tint):
        rgb = self.colors[theme]
        h, l, s = self.rgb_to_ms_hls(rgb)
        return self.rgb_to_hex(self.ms_hls_to_rgb(h, self.tint_luminance(tint, l), s))