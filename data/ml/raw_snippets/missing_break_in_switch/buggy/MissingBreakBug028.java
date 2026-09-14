package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug028 {
    static void describeLevel(int level) {
        switch (level) {
            case 1:
                System.out.println("Beginner");
                System.out.println("Try the tutorial first.");
                break;
            case 2:
                System.out.println("Intermediate");
                System.out.println("Practice loops and arrays.");
            case 3:
                System.out.println("Advanced");
                System.out.println("Build a full project.");
                break;
        }
    }
}
