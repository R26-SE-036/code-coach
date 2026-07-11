public class GenMissingBreakFix018 {
    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "closed";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}
