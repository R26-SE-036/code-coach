public class GenWhileNoUpdateFix002 {
    static void pump(boolean active, int quota) {
        while (!active) {
            System.out.println(quota);
            quota++;
            active = quota > 10;
        }
    }
}
