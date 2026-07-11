public class GenMissingBreakBug130 {
    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
            case 2:
                label = "active";
                break;
            case 3:
                label = "paid";
                break;
            case 4:
                label = "closed";
                break;
            default:
                label = "new";
        }
        return label;
    }
}
