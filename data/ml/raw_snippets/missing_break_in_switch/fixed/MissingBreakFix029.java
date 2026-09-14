package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix029 {
    static String label(int group, int item) {
        String result = "";
        switch (group) {
            case 1:
                switch (item) {
                    case 1:
                        result = "apple";
                        break;
                    case 2:
                        result = "banana";
                        break;
                    default:
                        result = "fruit";
                }
                break;
            case 2:
                result = "vegetable";
                break;
        }
        return result;
    }
}
