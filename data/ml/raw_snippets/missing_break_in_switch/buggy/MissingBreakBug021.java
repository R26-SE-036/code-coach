package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug021 {
    public static void main(String[] args) {
        String[] commands = { "start", "stop", "pause" };
        int running = 0;
        for (String command : commands) {
            switch (command) {
                case "start":
                    running = 1;
                    System.out.println("Started");
                case "stop":
                    running = 0;
                    System.out.println("Stopped");
                    break;
                case "pause":
                    System.out.println("Paused");
                    break;
            }
        }
        System.out.println(running);
    }
}
