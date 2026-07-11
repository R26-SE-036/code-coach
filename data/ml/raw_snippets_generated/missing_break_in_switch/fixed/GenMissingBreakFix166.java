public class GenMissingBreakFix166 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "draft";
                break;
            case 3:
                label = "expired";
                break;
            case 4:
                label = "new";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
