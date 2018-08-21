########################

########################


import maya.cmds as cmds
from functools import partial
import maya.mel as mel

import zTools.rig.zbw_rig as rig
import zTools.resources.zbw_window as zwin

#----------------one file should be softMod def, another should be softSelect (clusetr, jnt)
# USE THE WINDOW CLASS

widgets= {}
class SoftDeformerUI(zwin.Window):
    def __init__(self):
        super(SoftDeformerUI, self).__init__(title="Soft Mod Deformer", w=320, h=220, winName="softWin", buttonLabel="Create")

    def common_UI(self):
        self.softNameTFG = cmds.textFieldGrp(l="Deformer Name", w=300, cw=[(1, 100), (2, 190)], cal=[(1, "left"), (2, "left")], placeholderText="softMod_DEF")
        self.frontChainCBG = cmds.checkBoxGrp(l="Auto move to front of chain", v1=0, cw=[(1, 200)],cal=[(1, "left"), (2, "left")])
        self.ctrlScaleFFG = cmds.floatFieldGrp(l="Control Scale", v1=1, pre=2, cw=[(1, 150), (2, 50)], cal=[(1, "left"), (2, "left")])
        self.autoScaleCBG = cmds.checkBoxGrp(l="autoscale control?", v1=1, cw=[(1, 200)], cal=[(1, "left"), (2, "left")])
# TODO -  - do we need this?
        self.bindPoseIFG = cmds.intFieldGrp(l="BindPose/origin Frame", cw=[(1, 150), (2, 50)], cal=[(1, "left"), (2, "left")], v1=0)
        self.parentTFBG = cmds.textFieldButtonGrp(l="Parent Object:", cw=[(1, 75), (2, 175), (3, 75)], cal=[(1, "left"), (2, "left"), (3, "left")], bl="<<<", bc=self.set_parent_object)


    def custom_UI(self):
        pass


    def action(self, close, *args):
        # gather the data from UI
        smdName = cmds.textFieldGrp(self.softNameTFG, q=True, tx=True)
        foc = cmds.checkBoxGrp(self.frontChainCBG, q=True, v1=True)
        ctrlScl = cmds.floatFieldGrp(self.ctrlScaleFFG, q=True, v1=True)
        autoScale = cmds.checkBoxGrp(self.autoScaleCBG, q=True, v1=True)
        bindPoseFrame = cmds.intFieldGrp(self.bindPoseIFG, q=True, v1=True)
        parent = cmds.textFieldButtonGrp(self.parentTFBG, q=True, tx=True)
        # create the rig
        smdRig = SoftModRig(parent=parent, name=smdName, frontOfChain=foc, ctrlScale=ctrlScl, autoScale=autoScale, bindPoseFrame=bindPoseFrame)

        if close:
            self.close_window()


    def set_parent_object(self, *args):
        """
        gets selection and puts it in the given text field button grp
        """
        ctrl = None
        sel = cmds.ls(sl=True, type="transform", l=True)
        if sel:
            ctrl = sel[0]
        else:
            cmds.warning("need to select a transform as the parent object!")
            return()

        cmds.textFieldButtonGrp(self.parentTFBG, e=True, tx=ctrl)


class SoftModRig(object):
    def __init__(self, parent, name="softMod", frontOfChain=False, ctrlScale=1, autoScale=True, bindPoseFrame=0, obj=None):
        """
        only args REQUIRED is parent control (or follicle). Others are optional (obj to apply to (xform of mesh))
        """
        self.name = name
        self.frontOfChain = frontOfChain
        self.ctrlScale = ctrlScale
        self.autoScale = autoScale
        self.bindPoseFrame = bindPoseFrame
        self.parent = parent
        self.obj = obj
        self.initPos = None
        self.onSurface = False

        self.gather_info()


    def gather_info(self):
        if self.obj:
            if rig.type_check(self.obj, "mesh"):
                self.initPos = cmds.xform(self.obj, q=True, ws=True, rp=True)
            else:
                cmds.warning("Select only one polygon or verts from one polygon")
                return()

        if not self.obj:
            sel = cmds.ls(sl=True, fl=True)

            if sel:
                # check if using verts or the xform
                verts = cmds.filterExpand(sm=31)
                if verts:
                    # make sure vtx's just from one object
                    objList = [v.split(".")[0] for v in verts]
                    if len(set(objList))>1:
                        cmds.warning("need to select verts from only one object")
                        return()
                    self.initPos = rig.average_point_positions(verts)
                    self.obj = objList[0]
                    self.onSurface = True
                else:
                    if len(sel)>1:
                        cmds.warning("Select only one transform or verts from one transform")
                        return()
                    obj = sel[0]
                    if rig.type_check(obj, "mesh"):
                        self.initPos = cmds.xform(obj, q=True, ws=True, rp=True)
                        self.obj = obj
                    else:
                        cmds.warning("SoftModRig.gather_info: had an issue with your selection. Select only one polygon or verts from one polygon")
                        return()
            else:
                cmds.warning("Select only one polygon or verts from one polygon")
                return()

        self.create_soft_mod_rig()

    def create_soft_mod_rig(self):
        """
        create softmod rig on obj at initPosition, if self.onSurface: align to surface of obj
        """
        pos = (0, 0, 0)
        rot = (0, 0, 0)
        if self.onSurface:
            # get surface pos and rot
            pos = rig.closest_point_on_mesh_position(self.initPos, self.obj)
            rot = rig.closest_point_on_mesh_rotation(self.initPos, self.obj)

        # create controls
        self.baseGrp, self.baseCtrl, self.moveGrp, self.moveCtrl = self.create_controls(self.name)
        cmds.xform(self.baseGrp, ws=True, t=pos)
        cmds.xform(self.baseGrp, ws=True, ro=rot)

        # create softmod
        cmds.select(self.obj, r=True)
        self.softList = cmds.softMod(relative=False, falloffCenter=self.initPos, falloffRadius=5.0, n="{0}_softMod".format(self.name), frontOfChain=True)

        # link controls to softmod
        self.connect_ctrls_to_softmod()

        cmds.parent(self.baseGrp, self.parent)

    def connect_ctrls_to_softmod(self):
        cmds.addAttr(self.moveCtrl, ln="envelope", at="float", k=True, min=0, max=1, dv=1)
        cmds.addAttr(self.moveCtrl, ln="falloffRadius", at="float", k=True, min=0, dv=3.0)
        cmds.addAttr(self.moveCtrl, ln="mode", at="enum", enumName= "volume=0:surface=1", k=True)

        dm = cmds.shadingNode("decomposeMatrix", asUtility=True, name="{0}_dm".format(self.name))
        mm = cmds.shadingNode("multMatrix", asUtility=True, name="{0}_mm".format(self.name))
        falloffMult = cmds.shadingNode("multiplyDivide", asUtility=True, name="{0}_falloffMult".format(self.name))
        cmds.connectAttr("{0}.outputScale".format(dm), "{0}.input1".format(falloffMult))
        cmds.connectAttr("{0}.falloffRadius".format(self.moveCtrl), "{0}.input2.input2X".format(falloffMult))
        cmds.connectAttr("{0}.output.outputX".format(falloffMult), "{0}.falloffRadius".format(self.softList[0]), f=True)
        cmds.connectAttr("{0}.worldMatrix[0]".format(self.baseCtrl), "{0}.inputMatrix".format(dm))
        cmds.connectAttr("{0}.worldInverseMatrix[0]".format(self.baseCtrl), "{0}.postMatrix".format(self.softList[0]))
        cmds.connectAttr("{0}.worldMatrix[0]".format(self.baseCtrl), "{0}.preMatrix".format(self.softList[0]))
        cmds.connectAttr("{0}.worldMatrix[0]".format(self.moveCtrl), "{0}.matrixIn[0]".format(mm))
        cmds.connectAttr("{0}.parentInverseMatrix[0]".format(self.moveCtrl), "{0}.matrixIn[1]".format(mm))
        cmds.connectAttr("{0}.matrixSum".format(mm), "{0}.weightedMatrix".format(self.softList[0]))
        cmds.connectAttr("{0}.outputTranslate".format(dm), "{0}.falloffCenter".format(self.softList[0]))
        cmds.connectAttr("{0}.worldMatrix[0]".format(self.moveCtrl), "{0}.matrix".format(self.softList[0]), f=True)

        cmds.connectAttr("{0}.envelope".format(self.moveCtrl), "{0}.envelope".format(self.softList[0]), f=True)
        cmds.connectAttr("{0}.mode".format(self.moveCtrl), "{0}.falloffMode".format(self.softList[0]), f=True)

        cmds.setAttr("{0}.v".format(self.softList[1]), 0)
        cmds.parent(self.softList[1], self.moveCtrl)


    def create_controls(self, name):
        # size here
        baseCtrl = rig.create_control("{0}_base".format(name), type="cube", color="yellow")
        baseGrp = rig.group_freeze(baseCtrl)
        moveCtrl = rig.create_control("{0}_move".format(name), type="sphere", color="red")
        moveGrp = rig.group_freeze(moveCtrl)
        cmds.parent(moveGrp, baseCtrl)

        return(baseGrp, baseCtrl, moveGrp, moveCtrl)

# --------------------------
# softMod deformer
# --------------------------
# TODO - Add 'wave' to name . . .
def softWave(sftmod, arrow, ctrl,  *args):
    # add values to positions in graph
    positions = [0.0, 0.3, 0.6, 0.9, 0.95]
    values = [1.0, -0.3, 0.1, -0.05, 0.01]
    for i in range(len(positions)):
        cmds.setAttr("{0}.falloffCurve[{1}].falloffCurve_Position".format(sftmod, i), positions[i])
        cmds.setAttr("{0}.falloffCurve[{1}].falloffCurve_FloatValue".format(sftmod, i), values[i])
        cmds.setAttr("{0}.falloffCurve[{1}].falloffCurve_Interp".format(sftmod, i), 2)

    cmds.addAttr(arrow, ln="WaveAttrs", at="enum", k=True)
    cmds.setAttr("{0}.WaveAttrs".format(arrow), l=True)

    # expose these on the control
    for j in range(5):
        cmds.addAttr(arrow, ln="position{0}".format(j), at="float", min=0.0, max=1.0, dv=positions[j], k=True)
        cmds.connectAttr("{0}.position{1}".format(arrow, j),
                         "{0}.falloffCurve[{1}].falloffCurve_Position".format(sftmod, j))

    for j in range(5):
        cmds.addAttr(arrow, ln="value{0}".format(j), at="float", min=-1.0, max=1.0, dv=values[j], k=True)
        cmds.connectAttr("{0}.value{1}".format(arrow, j),
                         "{0}.falloffCurve[{1}].falloffCurve_FloatValue".format(sftmod, j))
        cmds.setAttr("{0}.position{1}".format(arrow, j), l=True)
        cmds.setAttr("{0}.value{1}".format(arrow, j), l=True)



def add_top_level_ctrl(origCtrl, type, geo, *args):
    """
    creates a new ctrl, orients it to the geo and parent constrains the orig ctrl rig under itself
    :param origCtrl: the control we're working from
    :param type: the ctrl type of shape see zbw_rig.createControl for options
    :param geo: the geo to orient to
    :param args:
    :return: topCtrl (the new ctrl), grp (the top ctrl grp freeze grp)
    """
    # THIS IS THE XTRA CTRL LAYER, THIS ORIENTS CTRL AND CONNECTS ORIG CTRL TO THE NEW CTRL
    origCtrlPos = cmds.xform(origCtrl, q=True, ws=True, rp=True)
    topCtrl = rig.create_control(name="{0}_moveCtrl".format(origCtrl.rpartition("_")[0]), type=type, axis="z",
                                 color="yellow")
    grp = rig.group_freeze(topCtrl)
    cmds.xform(grp, ws=True, t=origCtrlPos)
    nc = cmds.normalConstraint(geo, grp, worldUpType="vector", upVector=(0, 1, 0))
    cmds.delete(nc)
    pc = cmds.parentConstraint(topCtrl, origCtrl, mo=True)
    sc = cmds.scaleConstraint(topCtrl, origCtrl, mo=True)
    return(topCtrl, grp)


def create_soft_mod_deformer(wave=False, *args):
    """
    creates and sets up the softmod deformer
    """
# if vtx(s) seelected, put it there. Otherwise, jsut put it at the rp of the transform
# try undo decorator
##----------------position of control can come after. This should jsut be clean version, so we can call it from elsewhere
    bpf = cmds.intFieldGrp(widgets["bpFrameIFG"], q=True, v1=True)
    currentTime = cmds.currentTime(q=True)
    cmds.currentTime(bpf)

    check = cmds.checkBoxGrp(widgets["checkCBG"], q=True, v1=True)
    defName = cmds.textFieldGrp(widgets["smdTFG"], tx=True, q=True)
    scaleFactor = cmds.floatFieldGrp(widgets["scaleFFG"], q=True, v1=True)
    front = cmds.checkBoxGrp(widgets["frontCBG"], q=True, v1=True)
    auto = cmds.checkBoxGrp(widgets["autoscaleCBG"], q=True, v1=True)

    if (cmds.objExists(defName)):
        cmds.warning("An object of this name, {0}, already exists! Choose a new name!".format(defName))
        return()

# TODO - check that we've got only verts (or cv's?) selected - always do average?
    vertex = cmds.ls(sl=True, fl=True)
    if not vertex:
        cmds.warning("Must select at least one vertex")
        return()

    # get objects - in no parent object (to parent rig to) then parent to the object itself
    obj = vertex[0].partition(".")[0]

# TODO below is if we have a mesh . . . broaden to nurbs? or curve?
    if cmds.objectType(obj) == "mesh":
        obj = cmds.listRelatives(obj, p=True)[0]
    parentObject = cmds.textFieldButtonGrp(widgets["mainCtrlTFBG"], q=True, tx=True)
    if not parentObject:
        parentObject = obj

    vertPos = rig.average_point_positions(vertex)

    if check and (not front):
        deformer_check(obj)

    cmds.select(obj)
    softMod = defName
    softModAll = cmds.softMod(relative=False, falloffCenter=vertPos, falloffRadius=5.0, n=softMod,
                              frontOfChain=front)
    softmod = cmds.rename(softModAll[0], softMod)
    softModXform = cmds.listConnections(softModAll[0], type="transform")[0]

    ctrlName = defName + "_zeroed_GRP"
    control = cmds.group(name=ctrlName, em=True)

# TODO - make a little swatch to set the color of the control
    controlGrp = cmds.group(control, n="{0}_static_GRP".format(control.rpartition("_")[0]))
    cmds.xform(controlGrp, ws=True, t=vertPos)
    if wave:
        ctrlType = "arrow"
    else:
        ctrlType = "cube"
    topCtrl, topGrp = add_top_level_ctrl(control, ctrlType, cmds.listRelatives(obj, s=True)[0])

# TODO figure out how to transpose the space for just the scale
    rig.connect_transforms(control, softModXform)

    cmds.addAttr(topCtrl, ln="__XTRA__", at="enum", k=True)
    cmds.setAttr("{0}.__XTRA__".format(topCtrl), l=True)
    cmds.addAttr(topCtrl, ln="envelope", at="float", min=0, max=1, k=True, dv=1)
    cmds.addAttr(topCtrl, ln="falloff", at="float", min=0, max=100, k=True, dv=5)
    cmds.addAttr(topCtrl, ln="mode", at="enum", enumName= "volume=0:surface=1", k=True)

    # connect that attr to the softmod falloff radius
    cmds.connectAttr("{0}.envelope".format(topCtrl), "{0}.envelope".format(softMod))
    cmds.connectAttr("{0}.falloff".format(topCtrl), "{0}.falloffRadius".format(softMod))
    cmds.connectAttr("{0}.mode".format(topCtrl), "{0}.falloffMode".format(softMod))
    cmds.setAttr("{0}.inheritsTransform".format(softModXform), 0)
    cmds.setAttr("{0}.visibility".format(softModXform), 0)

    if auto:
        calsz = rig.calibrate_size(obj, .15)
        if calsz:
            rig.scale_nurbs_control(topCtrl, calsz, calsz, calsz)
            cmds.setAttr("{0}.falloff".format(topCtrl), 2*calsz)
        else:
            cmds.warning("I had an issue getting the calibrated scale of {0}".format(obj))
    rig.scale_nurbs_control(topCtrl, scaleFactor, scaleFactor, scaleFactor)

    defGroup = cmds.group(empty=True, n=(defName + "_deform_GRP"))
    cmds.xform(defGroup, ws=True, t=vertPos)
    cmds.parent(softModXform, controlGrp, defGroup)

# TODO - use the name of the deformer instead. . .
    masterGrp = cmds.group(name="{0}_mstr_GRP".format(obj), em=True)
    cmds.parent(topGrp, defGroup, masterGrp)

    if wave:
        softWave(softMod, topCtrl, control)

    cmds.parent(masterGrp, parentObject)

    newName = rig.increment_name(defName)
    cmds.textFieldGrp(widgets["smdTFG"], tx=newName, e=True)

    cmds.select(topCtrl)
    cmds.currentTime(currentTime)

    return (softMod, control, obj, defGroup)


#########
# joint stuff
#########
def soft_selection_to_joint(*args):
    """
    takes a soft selection of verts and creates a joint to bind & wieght them in that proportion
    :param args:
    :return: string - name of the soft sel joint we've created
    """
# again. . . make sure that this is clean, no UI stuff here - move entire code to zbw_rig?
# TODO -----  check for selection of verts!
    selVtx = cmds.ls(sl=True, fl=True) # to get center for joint
    vtxs, wts = rig.get_soft_selection() # to get weights for jnt

# TODO --- clean this up to not require the UI
    tform = vtxs[0].partition(".")[0]
    mesh = cmds.listRelatives(tform, s=True)[0]
    ptOnSurface = cmds.checkBoxGrp(widgets["jntCPOMCBG"], q=True, v1=True)
    auto = cmds.checkBoxGrp(widgets["jntAutoCBG"], q=True, v1=True)
    jntName = cmds.textFieldGrp(widgets["jntNameTFG"], q=True, tx=True)
    rotOnSurface = cmds.checkBoxGrp(widgets["jntRotCBG"], q=True, v1=True)

    cls = mel.eval("findRelatedSkinCluster " + tform)
    if not cls:
        if auto:
            baseJnt, cls = rig.new_joint_bind_at_center(tform)
        else:
            cmds.warning("There isn't an initial bind on this geometry. Either create one or check 'auto'")
            return()

    center = rig.average_point_positions(selVtx)
    rot = (0,0,0)
    if ptOnSurface:
        center = rig.closest_point_on_mesh_position(center, mesh)
    if rotOnSurface:
        rot = rig.closest_point_on_mesh_rotation(center, mesh)

    cmds.select(cl=True)
    jnt = cmds.joint(name = jntName)
    cmds.xform(jnt, ws=True, t=center)
    cmds.xform(jnt, ws=True, ro=rot)

    # add influence to skin Cluster
    cmds.select(tform, r=True)
    cmds.skinCluster(e=True, ai=jnt, wt=0)

    # apply weights to that joint
    for v in range(len(vtxs)):
        cmds.skinPercent(cls, vtxs[v], transformValue=[jnt, wts[v]])

    newName = rig.increment_name(jntName)
    cmds.textFieldGrp(widgets["jntNameTFG"], tx=newName, e=True)

    return(jnt)


def softDeformer():
    """Use this to start the script!"""
    sd = SoftDeformerUI()
