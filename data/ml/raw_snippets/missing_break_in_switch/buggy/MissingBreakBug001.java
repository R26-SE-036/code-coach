package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug001 {
    static String dayName(int day) {
        String name;
        switch (day) {
            case 1:
                name = "Monday";
                break;
            case 2:
                name = "Tuesday";
            case 3:
                name = "Wednesday";
                break;
            default:
                name = "Unknown";
        }
        return name;
    }
}
