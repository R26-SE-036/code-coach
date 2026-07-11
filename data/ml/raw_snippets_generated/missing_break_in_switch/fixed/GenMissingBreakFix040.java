public class GenMissingBreakFix040 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "shipped";
                break;
            case 4:
                label = "new";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
