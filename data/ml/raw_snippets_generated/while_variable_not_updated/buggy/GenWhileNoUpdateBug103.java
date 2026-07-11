public class GenWhileNoUpdateBug103 {
    static void pump(boolean armed, int quota) {
        while (!armed) {
            System.out.println(quota);
            quota++;
        }
    }
}
