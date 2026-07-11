public class GenCleanGeneric091 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
