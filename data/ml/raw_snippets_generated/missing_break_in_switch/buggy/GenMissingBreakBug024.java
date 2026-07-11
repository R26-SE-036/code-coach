public class GenMissingBreakBug024 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "archived";
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
