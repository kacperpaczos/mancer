import os
import subprocess
from pathlib import Path

from textual.app import App
from textual.containers import Container, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Label, ListItem, ListView, Static


class StatusBar(Static):
    def on_mount(self):
        self.update_status()

    def update_status(self):
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "nginx"], capture_output=True, text=True
            )
            status = result.stdout.strip()
            color = "green" if status == "active" else "red"
            self.update(f"[{color}]Nginx Status: {status}[/]")
        except Exception as e:
            self.update(f"[red]Error checking nginx status: {str(e)}[/]")


class ApplicationList(ListView):
    def on_mount(self):
        self.load_applications()

    def load_applications(self):
        nginx_path = Path("/etc/nginx/sites-available")
        try:
            self.clear()
            self.append(ListItem(Label("nginx.conf [Main configuration]")))

            apps = [site.name for site in nginx_path.glob("*") if site.is_file()]
            for app in sorted(apps):
                if app == "default":
                    self.append(ListItem(Label("default [Default page]")))
                else:
                    self.append(ListItem(Label(app)))
        except Exception as e:
            self.append(ListItem(Label(f"[red]Error loading applications: {str(e)}[/]")))


class ManagementScreen(Screen):
    def compose(self):
        yield Container(
            StatusBar(id="status_bar"),
            ScrollableContainer(ApplicationList(id="app_list"), id="apps_container"),
            Button("Back to menu", id="back_button"),
            id="management_container",
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        app_name = event.item.children[0].renderable
        self.app.push_screen(AppDetailsScreen(app_name))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_button":
            self.app.pop_screen()


class AppDetailsScreen(Screen):
    def __init__(self, app_name: str):
        super().__init__()
        self.app_name = app_name.split(" ")[0]

    def compose(self):
        yield Container(
            StatusBar(id="status_bar"),
            Static(f"Application details: {self.app_name}", id="app_title"),
            Container(
                Button("Show config", id="show_config"),
                Button("Edit config", id="edit_config"),
                Button("Check status", id="check_status"),
                Button("Enable/Disable", id="toggle_app"),
                Button("Back", id="back_button"),
                id="actions_container",
            ),
            ScrollableContainer(Static(id="details_content"), id="scroll_container"),
            id="app_details_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_button":
            self.app.pop_screen()
        elif event.button.id == "show_config":
            self.show_config()
        elif event.button.id == "edit_config":
            self.edit_config()
        elif event.button.id == "check_status":
            self.check_status()
        elif event.button.id == "toggle_app":
            self.toggle_app()

    def show_config(self):
        try:
            if self.app_name == "nginx.conf":
                config_path = "/etc/nginx/nginx.conf"
            else:
                config_path = f"/etc/nginx/sites-available/{self.app_name}"

            if not os.path.exists(config_path):
                self.query_one("#details_content").update(
                    f"[red]Error: File {config_path} does not exist[/]"
                )
                return

            with open(config_path, "r") as f:
                content = f.read()
            self.query_one("#details_content").update(f"```\n{content}\n```")
        except PermissionError:
            self.query_one("#details_content").update(
                "[red]Error: Permission denied. Please run the application with sudo.[/]"
            )
        except Exception as e:
            self.query_one("#details_content").update(f"[red]Config read error: {str(e)}[/]")

    def edit_config(self):
        try:
            if self.app_name == "nginx.conf":
                config_path = "/etc/nginx/nginx.conf"
            else:
                config_path = f"/etc/nginx/sites-available/{self.app_name}"

            if not os.path.exists(config_path):
                self.query_one("#details_content").update(
                    f"[red]Error: File {config_path} does not exist[/]"
                )
                return

            # Try to check write permissions
            if not os.access(config_path, os.W_OK):
                self.query_one("#details_content").update(
                    "[red]Error: Permission denied. Please run the application with sudo.[/]"
                )
                return

            # Open file in default editor
            editor = os.environ.get("EDITOR", "nano")
            subprocess.run([editor, config_path])
            self.query_one("#details_content").update(
                "[green]Config file opened in editor. Please check nginx configuration after editing.[/]"
            )
        except Exception as e:
            self.query_one("#details_content").update(f"[red]Edit error: {str(e)}[/]")

    def check_status(self):
        if self.app_name == "nginx.conf":
            self.query_one("#details_content").update("Status: Main configuration file")
            return

        enabled_path = Path(f"/etc/nginx/sites-enabled/{self.app_name}")
        status = "Enabled" if enabled_path.exists() else "Disabled"
        self.query_one("#details_content").update(f"Status: {status}")

    def toggle_app(self):
        if self.app_name == "nginx.conf":
            self.query_one("#details_content").update(
                "[yellow]Cannot enable/disable main configuration file[/]"
            )
            return

        try:
            enabled_path = f"/etc/nginx/sites-enabled/{self.app_name}"
            available_path = f"/etc/nginx/sites-available/{self.app_name}"
            if os.path.exists(enabled_path):
                os.unlink(enabled_path)
                status = "disabled"
            else:
                os.symlink(available_path, enabled_path)
                status = "enabled"
            self.query_one("#details_content").update(f"Application has been {status}")
            subprocess.run(["systemctl", "reload", "nginx"])
        except Exception as e:
            self.query_one("#details_content").update(f"[red]Toggle error: {str(e)}[/]")


class MainScreen(Screen):
    def compose(self):
        yield Container(
            StatusBar(id="status_bar"),
            Container(
                Button("Overseer", id="overseer_button", classes="menu_button"),
                Button("Management", id="management_button", classes="menu_button"),
                id="main_container",
            ),
            id="root_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "overseer_button":
            self.app.push_screen(OverseerScreen())
        elif event.button.id == "management_button":
            self.app.push_screen(ManagementScreen())


class OverseerScreen(Screen):
    def compose(self):
        yield Container(
            StatusBar(id="status_bar"),
            Button("Back to menu", id="back_button"),
            id="overseer_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_button":
            self.app.pop_screen()


class NOMApp(App):
    CSS = """
    #root_container {
        layout: vertical;
        height: 100%;
    }

    #status_bar {
        height: 1;
        dock: top;
        padding: 0 1;
        background: $surface;
    }

    #main_container {
        layout: horizontal;
        height: 100%;
        align: center middle;
    }
    
    .menu_button {
        width: 50%;
        height: 3;
        margin: 1;
    }
    
    #management_container, #overseer_container {
        layout: vertical;
        height: 100%;
    }

    #apps_container {
        height: 1fr;
        border: solid $accent;
        margin: 1;
    }
    
    #app_title {
        text-align: center;
        padding: 1;
    }
    
    #actions_container {
        layout: horizontal;
        align: center middle;
        padding: 1;
        height: auto;
        background: $surface;
    }

    #actions_container Button {
        margin: 0 1;
    }
    
    #scroll_container {
        height: 1fr;
        border: solid $accent;
        margin: 1;
        overflow-y: scroll;
    }

    #details_content {
        padding: 1;
        width: 100%;
    }

    #app_details_container {
        layout: vertical;
        height: 100%;
    }
    """

    def on_mount(self):
        self.push_screen(MainScreen())


if __name__ == "__main__":
    app = NOMApp()
    app.run()
