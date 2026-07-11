public class GenMissingBreakFix162 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "final";
                break;
            case 3:
                label = "closed";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}
