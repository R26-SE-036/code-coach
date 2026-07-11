public class GenCleanGeneric048 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "new";
        }
        return label;
    }
}
