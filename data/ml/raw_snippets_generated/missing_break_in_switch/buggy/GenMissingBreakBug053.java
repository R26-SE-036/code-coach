public class GenMissingBreakBug053 {
    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "active";
            case 3:
                label = "archived";
                break;
            case 4:
                label = "draft";
                break;
            case 5:
                label = "queued";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
