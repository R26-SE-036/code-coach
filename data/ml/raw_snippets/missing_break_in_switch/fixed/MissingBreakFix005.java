package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix005 {
    static String nextLight(String current) {
        String next = "";
        switch (current) {
            case "RED":
                next = "GREEN";
                break;
            case "GREEN":
                next = "YELLOW";
                break;
            case "YELLOW":
                next = "RED";
                break;
        }
        return next;
    }
}
