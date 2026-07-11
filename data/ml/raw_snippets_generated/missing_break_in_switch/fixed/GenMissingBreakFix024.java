public class GenMissingBreakFix024 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "expired";
                break;
            case 4:
                label = "draft";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
