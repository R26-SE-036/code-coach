public class GenMissingBreakBug097 {
    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "paid";
            case 3:
                label = "shipped";
                break;
            case 4:
                label = "new";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}
