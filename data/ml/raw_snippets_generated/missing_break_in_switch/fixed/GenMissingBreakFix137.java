public class GenMissingBreakFix137 {
    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "paid";
                break;
            case 3:
                label = "archived";
                break;
            case 4:
                label = "draft";
                break;
            case 5:
                label = "closed";
                break;
            default:
                label = "expired";
        }
        return label;
    }
}
