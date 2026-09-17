package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug005 {
    static String nextLight(String current) {
        String next = "";
        switch (current) {
            case "RED":
                next = "GREEN";
                break;
            case "GREEN":
                next = "YELLOW";
            case "YELLOW":
                next = "RED";
                break;
        }
        return next;
    }
}
