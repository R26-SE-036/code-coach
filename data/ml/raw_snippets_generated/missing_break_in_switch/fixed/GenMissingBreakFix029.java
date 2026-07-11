public class GenMissingBreakFix029 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "expired";
                break;
            case 4:
                label = "archived";
                break;
            default:
                label = "new";
        }
        return label;
    }
}
