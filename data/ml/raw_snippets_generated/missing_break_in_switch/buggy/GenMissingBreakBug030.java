public class GenMissingBreakBug030 {
    static String describeItem(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "queued";
            case 3:
                label = "new";
                break;
            case 4:
                label = "draft";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
