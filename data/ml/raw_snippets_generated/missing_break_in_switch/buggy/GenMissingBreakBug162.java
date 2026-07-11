public class GenMissingBreakBug162 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "final";
            case 3:
                label = "closed";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}
