public class GenMissingBreakFix011 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "closed";
                break;
            case 4:
                label = "active";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}
