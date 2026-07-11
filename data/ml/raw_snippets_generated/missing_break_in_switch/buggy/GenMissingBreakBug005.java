public class GenMissingBreakBug005 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "active";
            case 3:
                label = "closed";
                break;
            case 4:
                label = "new";
                break;
            case 5:
                label = "paid";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}
