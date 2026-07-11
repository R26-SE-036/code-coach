public class GenMissingBreakFix026 {
    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }

    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "draft";
                break;
            case 3:
                label = "archived";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
