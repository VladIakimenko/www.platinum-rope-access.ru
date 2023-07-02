def format_response(message, error=None):
        frame_color = "red" if error else "blue"
        return (
            f'<div style="display: flex;'
            f'justify-content: center;'
            f'align-items: center;'
            f'height: 100vh;">'
            f'<div style="border: 1px solid {frame_color}; padding: 10px;">'
            f'<h5 style="color: black; font-weight: bold;">'
            f'{message}'
            f'</h5></div></div>'
        )