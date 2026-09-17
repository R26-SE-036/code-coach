package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug019 {
    static String planet(int position) {
        switch (position) {
            case 1:
                return "Mercury";
            case 2:
                return "Venus";
            case 3:
                System.out.println("Home");
            case 4:
                return "Mars";
            default:
                return "Unknown";
        }
    }
}
