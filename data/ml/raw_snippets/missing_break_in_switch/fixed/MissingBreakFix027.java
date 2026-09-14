package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix027 {
    static boolean isWeekend(String day) {
        boolean weekend = false;
        switch (day) {
            case "Saturday":
            case "Sunday":
                weekend = true;
                break;
            case "Monday":
                weekend = false;
                break;
            default:
                weekend = false;
        }
        return weekend;
    }
}
