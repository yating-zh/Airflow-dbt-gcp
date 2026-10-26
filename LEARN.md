# Commands Used

Commands run while setting up the Astro project and checking Docker (updated 2026-10-24):

1. `docker --version` — confirmed Docker CLI version `29.8.2`.
2. `docker info` — checked Docker Engine; the initial output showed an HTTP 500 server error.
3. `astro version` — returned `command not found` on the first attempt; after shell history was restored, it reported Astro CLI version `1.46.1`.
4. `astro --version` — returned `command not found` on the first attempt.
5. `astro version` — reported Astro CLI version `1.46.1`.
6. `astro dev init` — initialized an Astro project in the current folder.
7. `astro start` — failed because `start` is not a top-level Astro command.
8. `astro dev start` — updated the project image, then failed with `unexpected EOF`.
9. `astro dev start` — updated the project image and displayed “Project is starting up…”.
10. `astro dev start` — failed with `timed out waiting for docker` while Docker Engine was unavailable.
11. `astro dev start` — failed to mount the project DAG folder from iCloud Drive with `operation not permitted`.
12. `astro dev start` — completed successfully (exit code `0`) after Docker gained access to the project files.
