package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix019 {
    static String planet(int position) {
        switch (position) {
            case 1:
                return "Mercury";
            case 2:
                return "Venus";
            case 3:
                System.out.println("Home");
                return "Earth";
            case 4:
                return "Mars";
            default:
                return "Unknown";
        }
    }
}
