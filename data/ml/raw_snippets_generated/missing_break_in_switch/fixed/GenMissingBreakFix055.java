public class GenMissingBreakFix055 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "draft";
                break;
            case 3:
                label = "shipped";
                break;
            case 4:
                label = "paid";
                break;
            case 5:
                label = "expired";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
