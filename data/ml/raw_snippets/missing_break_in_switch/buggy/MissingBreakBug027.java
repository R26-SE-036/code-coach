package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug027 {
    static boolean isWeekend(String day) {
        boolean weekend = false;
        switch (day) {
            case "Saturday":
            case "Sunday":
                weekend = true;
            case "Monday":
                weekend = false;
                break;
            default:
                weekend = false;
        }
        return weekend;
    }
}
