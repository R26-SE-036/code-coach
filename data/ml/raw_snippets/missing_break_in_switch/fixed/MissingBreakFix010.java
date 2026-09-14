package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix010 {
    static String statusText(int code) {
        String text;
        switch (code) {
            case 200:
                text = "OK";
                break;
            case 404:
                text = "Not Found";
                break;
            case 500:
                text = "Server Error";
                break;
            default:
                text = "Unknown";
                break;
        }
        return text;
    }
}
